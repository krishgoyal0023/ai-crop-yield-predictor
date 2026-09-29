"""
Training entry point
Run this to train the yield prediction model
"""

import sys
from pathlib import Path
import logging
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data.loader import DataLoader
from backend.data.cleaner import DataCleaner
from backend.model.features import FeatureEngineer
from backend.model.train import ModelTrainer
from backend.model.predictor import YieldPredictor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run complete training pipeline."""
    logger.info("="*80)
    logger.info("PUNJAB CROP YIELD PREDICTION - TRAINING PIPELINE")
    logger.info("="*80)

    # Create directories
    Path("data").mkdir(exist_ok=True)
    Path("models").mkdir(exist_ok=True)

    # Step 1: Load data
    logger.info("\n[1/6] Loading data...")
    loader = DataLoader(data_dir="data")
    yield_df = loader.load_yield_data()
    soil_df = loader.load_soil_data()

    quality_report = loader.validate_data_quality(yield_df)
    logger.info(f"Data quality: {quality_report}")

    # Step 2: Clean data
    logger.info("\n[2/6] Cleaning data...")
    cleaner = DataCleaner()
    yield_df, cleaning_report = cleaner.clean_pipeline(
        yield_df,
        required_cols=["Year", "District", "Crop", "Season", "Area", "Yield"]
    )
    logger.info(f"Cleaning report: {cleaning_report}")

    # Step 3: Engineer features
    logger.info("\n[3/6] Engineering features...")
    engineer = FeatureEngineer()
    feature_df = engineer.engineer_features(yield_df, soil_df, is_training=True)

    feature_list = engineer.get_feature_list(feature_df)
    logger.info(f"Feature list ({len(feature_list)} features): {feature_list}")

    # Step 4: Train models (ablation study)
    logger.info("\n[4/6] Training models (ablation study)...")
    trainer = ModelTrainer(model_dir="models")
    results = trainer.train_ablation_ladder(feature_df, engineer)

    # Print results
    trainer.print_ablation_results(results)

    # Step 5: Train per-crop models
    logger.info("\n[5/6] Training per-crop models...")
    per_crop_results = trainer.train_per_crop_models(feature_df, engineer)

    # Step 6: Save baselines and artifacts
    logger.info("\n[6/6] Saving artifacts...")

    # Save predictor with baselines
    predictor = YieldPredictor(model_dir="models")
    predictor._save_baselines(feature_df)

    # Save feature importance report
    if "lightgbm" in trainer.models:
        model = trainer.models["lightgbm"]
        importance = trainer.get_feature_importance(model, feature_list)

        importance_path = Path("models") / "feature_importance.csv"
        importance.to_csv(importance_path, index=False)
        logger.info(f"Saved feature importance to {importance_path}")
        logger.info("\nTop 10 features:")
        for _, row in importance.head(10).iterrows():
            logger.info(f"  {row['feature']:30s}: {row['importance']:.4f}")

    # Save full results
    results_path = Path("models") / "training_results.json"
    # Convert numpy types for JSON serialization
    results_serializable = {}
    for model_name, data in results.items():
        results_serializable[model_name] = {
            "num_features": data["num_features"],
            "features": data["features"],
            "best_model": data["best_model"],
            "models": {}
        }
        for algo, metrics in data["models"].items():
            results_serializable[model_name]["models"][algo] = {
                k: v for k, v in metrics.items() if k != "predictions"
            }

    with open(results_path, "w") as f:
        json.dump(results_serializable, f, indent=2)
    logger.info(f"Saved training results to {results_path}")

    logger.info("\n" + "="*80)
    logger.info("TRAINING COMPLETE!")
    logger.info("="*80)
    logger.info(f"\nModels saved to: models/")
    logger.info(f"To run the API: uvicorn app:app --reload --port 8000")
    logger.info(f"To view results: cat models/training_results.json")

    return results


if __name__ == "__main__":
    main()
