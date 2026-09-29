
export default function MapPicker({ onLocationSelect, position }) {
  const lat = position ? position[0] : 31.0;
  const lon = position ? position[1] : 75.5;
  const bbox = `${lon - 1.5},${lat - 1},${lon + 1.5},${lat + 1}`;

  return (
    <div style={{ height: '400px', width: '100%', borderRadius: '0.75rem', overflow: 'hidden', position: 'relative' }}>
      <iframe
        title="Punjab Map"
        src={`https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lon}`}
        style={{ border: 0, width: '100%', height: '100%' }}
        allowFullScreen
        loading="lazy"
      />
      <div style={{
        position: 'absolute', bottom: 10, left: 10, right: 10,
        background: 'rgba(255,255,255,0.9)', padding: '8px 12px',
        borderRadius: '8px', fontSize: '12px', color: '#555',
        lineHeight: '1.4'
      }}>
        <strong>Visual reference only</strong> — Enter coordinates in the form to set your field location, or use GPS.
      </div>
    </div>
  );
}
