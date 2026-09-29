"""
Farm intelligence services.
Transparent rule-based decision support for fertilizer, irrigation, disease risk,
economics, crop rotation and a local agronomy assistant.
"""
from datetime import date, timedelta
from typing import Dict, Optional
import requests

MSP_2026_27 = {
    "Wheat": {"price_per_quintal": 2585, "season": "RMS 2026-27"},
    "Rice": {"price_per_quintal": 2441, "season": "KMS 2026-27", "grade_a": 2461},
    "Maize": {"price_per_quintal": 2410, "season": "KMS 2026-27"},
    "Gram": {"price_per_quintal": 5875, "season": "RMS 2026-27"},
    "Mustard": {"price_per_quintal": 6200, "season": "RMS 2026-27"},
    "Lentil": {"price_per_quintal": 7000, "season": "RMS 2026-27"},
}

def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def fertilizer_recommendation(crop: str, soil: Dict, area_ha: float = 1.0,
                              target_yield_t_ha: Optional[float] = None,
                              previous_crop: Optional[str] = None,
                              lcc: Optional[float] = None) -> Dict:
    """Uses PAU-oriented transparent rules. Soil-test values are preferred."""
    crop = crop.title()
    acres = area_ha * 2.47105
    p = _num(soil.get("P", soil.get("phosphorus")), None)
    k = _num(soil.get("K", soil.get("potassium")), None)
    n = _num(soil.get("N", soil.get("nitrogen")), None)
    steps = []
    if crop == "Wheat":
        dap = 55.0
        if p is not None:
            if p > 20: dap = 0
            elif p < 5: dap = 68.75
            elif p < 9: dap = 55
            else: dap = 41.25
        if lcc is not None:
            urea_first = 15 if lcc > 5 else 30 if lcc >= 4.5 else 40 if lcc >= 4 else 55
        else:
            urea_first = 40
        if previous_crop and previous_crop.title() == "Wheat":
            steps.append("Previous crop is wheat: verify nitrogen requirement with soil/LCC before increasing urea.")
        if k is not None and k < 120:
            mop = 20
        else:
            mop = 0
        steps += [
            f"Basal DAP: {dap:.1f} kg/acre.",
            f"Urea at first irrigation: about {urea_first:.1f} kg/acre; use PAU-LCC where available.",
            f"MOP/potash: {mop:.1f} kg/acre based on the supplied K status.",
        ]
        return {
            "crop": crop, "area_acres": round(acres, 2),
            "recommendations_per_acre": {"DAP_kg": round(dap,1), "Urea_kg": round(urea_first,1), "MOP_kg": round(mop,1)},
            "total_for_field_kg": {"DAP": round(dap*acres,1), "Urea": round(urea_first*acres,1), "MOP": round(mop*acres,1)},
            "basis": "PAU wheat fertilizer/LCC guidance; soil-test values override generic assumptions.",
            "steps": steps,
            "caution": "Do not treat SoilGrids estimates as a laboratory soil test. Recheck nutrient status before a high-value application."
        }
    if crop == "Rice":
        p_action = "Omit routine phosphorus if the preceding wheat crop received its recommended phosphorus dose; otherwise use soil-test guidance."
        steps = [p_action, "Use nitrogen judiciously and split applications; PAU recommends soil testing/LCC-based management.", "Avoid excessive nitrogen because it can increase pest/disease pressure."]
        return {
            "crop": crop, "area_acres": round(acres,2),
            "recommendations_per_acre": {"DAP_kg": None, "Urea_kg": None, "MOP_kg": None},
            "total_for_field_kg": {"DAP": None, "Urea": None, "MOP": None},
            "basis": "PAU Kharif package: rice fertilizer should be soil-test/management based rather than a blind fixed dose.",
            "steps": steps,
            "caution": "Enter a current soil test/LCC result to unlock a numeric rice fertilizer plan."
        }
    raise ValueError("Supported crops: Wheat, Rice")

def irrigation_schedule(lat: float, lon: float, crop: str, stage: str,
                        area_ha: float = 1.0, efficiency: float = 0.75,
                        pump_lpm: Optional[float] = None) -> Dict:
    params = {
        "latitude": lat, "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max,et0_fao_evapotranspiration",
        "forecast_days": 7, "timezone": "Asia/Kolkata"
    }
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=12)
    r.raise_for_status()
    d = r.json().get("daily", {})
    kc_map = {
        "Wheat": {"sowing": .45, "tillering": .75, "midseason": 1.15, "flowering": 1.15, "grain_fill": .90, "preharvest": .65},
        "Rice": {"sowing": 1.05, "tillering": 1.10, "midseason": 1.20, "flowering": 1.20, "grain_fill": 1.05, "preharvest": .90},
    }
    kc = kc_map.get(crop.title(), {}).get(stage.lower(), .9)
    rows=[]
    for i, ds in enumerate(d.get("time", [])):
        et0=_num(d.get("et0_fao_evapotranspiration",[0]*len(d.get("time",[])))[i])
        rain=_num(d.get("precipitation_sum",[0]*len(d.get("time",[])))[i])
        etc=et0*kc
        effective_rain=min(rain, etc*0.8)
        net=max(0, etc-effective_rain)/max(efficiency,.1)
        volume_m3=net*area_ha*10
        runtime_min=(volume_m3*1000/pump_lpm) if pump_lpm and pump_lpm>0 else None
        rows.append({"date":ds,"et0_mm":round(et0,2),"rain_mm":round(rain,2),"kc":kc,
                     "crop_et_mm":round(etc,2),"irrigation_mm":round(net,2),
                     "water_m3":round(volume_m3,1),"pump_runtime_min":round(runtime_min,1) if runtime_min else None})
    return {"source":"Open-Meteo FAO-56 ET0","crop":crop,"stage":stage,"area_ha":area_ha,
            "efficiency":efficiency,"schedule":rows,
            "note":"ET0 is reference evapotranspiration. Kc and application efficiency are assumptions; adjust them to local agronomy, soil and irrigation method."}

def disease_risk(crop: str, forecast: Dict, stage: str = "midseason") -> Dict:
    days=forecast.get("schedule", forecast.get("daily", []))
    risks=[]
    for row in days:
        t=(row.get("temperature_max") or row.get("temp_max") or 0)
        rain=(row.get("rain_mm") or row.get("precipitation") or 0)
        rh=(row.get("humidity") or row.get("relative_humidity") or 0)
        name="General"
        score=0
        reason=[]
        if crop.title()=="Wheat":
            name="Yellow rust"
            if 10 <= t <= 22: score += 35; reason.append("temperature in a conducive range")
            if rh >= 70: score += 35; reason.append("high humidity")
            if rain >= 1: score += 20; reason.append("recent/forecast rain")
        elif crop.title()=="Rice":
            name="Sheath blight"
            if 25 <= t <= 34: score += 30; reason.append("warm conditions")
            if rh >= 80: score += 40; reason.append("high humidity")
            if rain >= 3: score += 20; reason.append("rain/wet canopy conditions")
        score=min(score,100)
        level="High" if score>=70 else "Moderate" if score>=40 else "Low"
        risks.append({"date":row.get("date"),"disease":name,"risk_score":score,"risk_level":level,"why":reason})
    return {"crop":crop,"stage":stage,"risks":risks,
            "disclaimer":"Weather risk is an early-warning signal, not a diagnosis. Inspect the crop and follow current PAU/extension advisories before spraying."}

def economics(crop: str, predicted_yield_t_ha: float, area_ha: float,
              sale_price_per_quintal: Optional[float]=None,
              costs_per_ha: Optional[Dict[str,float]]=None) -> Dict:
    msp=MSP_2026_27.get(crop.title())
    price=_num(sale_price_per_quintal, msp["price_per_quintal"] if msp else 0)
    production_q=predicted_yield_t_ha*10*area_ha
    revenue=production_q*price
    costs=costs_per_ha or {}
    total_cost=sum(_num(v) for v in costs.values())*area_ha
    return {"crop":crop,"area_ha":area_ha,"production_quintals":round(production_q,2),
            "price_per_quintal":price,"price_basis":"User price" if sale_price_per_quintal else f"Government MSP {msp['season']}" if msp else "User price required",
            "gross_revenue":round(revenue,2),"cost_breakdown":costs,"total_cost":round(total_cost,2),
            "net_profit":round(revenue-total_cost,2),"msp_reference":msp}

def rotation_suggestions(crop: str, water_available: str="normal") -> Dict:
    c=crop.title()
    if c=="Rice":
        choices=[
            {"crop":"Maize","reason":"Alternative kharif cereal; can reduce dependence on puddled rice where suitable."},
            {"crop":"Moong","reason":"Short-duration pulse option after/around suitable rotations."},
            {"crop":"Soybean","reason":"Oilseed/legume option where soil, market and water conditions permit."},
        ]
    else:
        choices=[
            {"crop":"Maize","reason":"Kharif cereal option for diversification where water and market access permit."},
            {"crop":"Moong","reason":"Pulse option that can diversify a rice-wheat system."},
            {"crop":"Mustard","reason":"Rabi oilseed alternative where sowing window and soil fit."},
        ]
    return {"current_crop":crop,"water_available":water_available,"alternatives":choices,
            "note":"Rotation choices must be checked against sowing window, soil, irrigation, local market and current PAU recommendations."}

def agronomist_answer(question: str, crop: str, stage: str, soil: Dict, weather: Dict) -> Dict:
    q=question.lower()
    if "fertil" in q or "urea" in q or "dap" in q:
        answer="Use the Fertilizer module with a recent soil test. For wheat, PAU guidance supports soil/LCC-based nitrogen management and phosphorus decisions based on soil status; avoid blindly increasing urea."
    elif "water" in q or "irrig" in q:
        answer="Use the 7-day irrigation schedule. It estimates crop demand from forecast FAO-56 ET0, rainfall and a crop-stage coefficient; field soil moisture and irrigation efficiency still need to be considered."
    elif "disease" in q or "rust" in q or "pest" in q:
        answer="The disease module is a weather-risk warning, not a diagnosis. Inspect the field and compare symptoms with current PAU/extension advisories before any pesticide decision."
    elif "price" in q or "profit" in q or "msp" in q:
        answer="The market module separates MSP from a user-entered sale price and calculates gross revenue and costs. MSP is not a guarantee that every market transaction occurs at that price."
    else:
        answer=f"For {crop} at {stage}, combine the yield estimate with soil, weather and field observations. I can currently help with fertilizer, irrigation, disease-risk and profitability questions."
    return {"answer":answer,"context":{"crop":crop,"stage":stage,"soil_source":soil.get("source"),"weather_source":weather.get("source")},"sources":["PAU Package of Practices","Open-Meteo weather/ET0","Government of India MSP notifications"]}

def ndvi_status() -> Dict:
    return {"available":False,"provider":"Copernicus Data Space / Sentinel-2","required_env":["COPERNICUS_CLIENT_ID","COPERNICUS_CLIENT_SECRET"],
            "message":"NDVI integration is prepared for Sentinel-2 B04/B08 but requires Copernicus credentials. No fake NDVI values are returned."}
