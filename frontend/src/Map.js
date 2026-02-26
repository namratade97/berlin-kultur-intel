import React, { useState } from 'react';
import Map, { Marker, Popup, NavigationControl } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import { Copy, ExternalLink, MapPin } from 'lucide-react';
import 'maplibre-gl/dist/maplibre-gl.css';

const MAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";

// based on our collected datapoints
const COLLECTION_COLORS = {
  FebruaryEvents: '#3b82f6',
  MarchEvents: '#10b981',
  AprilEvents: '#f59e0b',
  ExhibitionEvents: '#ab119bff',
  FestivalEvents: '#b59bffff'
};

function MapView({ events }) {
  const [selectedEvent, setSelectedEvent] = useState(null);

  const copyToClipboard = (e, text) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    alert("Coordinates copied to clipboard!");
  };

  return (
    <div style={{ width: '72%', height: '100vh' }}>
      <Map
        mapLib={maplibregl}
        initialViewState={{ longitude: 13.405, latitude: 52.52, zoom: 11 }}
        mapStyle={MAP_STYLE}
      >
        <NavigationControl position="top-left" />

        {events && events.map((event, i) => (
          <React.Fragment key={i}>
            <Marker longitude={event.lng} latitude={event.lat} anchor="bottom">
              <div 
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedEvent(event);
                }}
                style={{ 
                  backgroundColor: COLLECTION_COLORS[event.collection] || '#7c3aed',
                  width: '20px', 
                  height: '20px', 
                  borderRadius: '50%', 
                  border: '2px solid white', 
                  cursor: 'pointer', 
                  boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
                  transition: 'transform 0.2s'
                }} 
                onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.2)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
              />
            </Marker>

            
            {selectedEvent === event && (
              <Popup
                longitude={event.lng}
                latitude={event.lat}
                anchor="top"
                onClose={() => setSelectedEvent(null)}
                closeOnClick={false}
                style={{ zIndex: 10 }}
              >
                <div style={{ padding: '10px', maxWidth: '240px', fontSize: '13px', color: '#1f2937' }}>
                  <b style={{ display: 'block', color: '#7c3aed', marginBottom: '4px', fontSize: '15px' }}>
                    {event.eventName}
                  </b>
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', fontWeight: '600', color: '#6b7280', marginBottom: '8px' }}>
                    <MapPin size={12} />
                    {event.venueName} {event.district ? `• ${event.district}` : ''}
                  </div>
                  
                  {event.summary && event.summary.length > 5 ? (
                    <p style={{ margin: '8px 0', color: '#374151', lineHeight: '1.4' }}>
                      {event.summary}
                    </p>
                  ) : null}

                  {/* Coordinates & Copy Feature */}
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between', 
                    marginTop: '12px', 
                    paddingTop: '8px', 
                    borderTop: '1px solid #e5e7eb' 
                  }}>
                    <code style={{ fontSize: '11px', color: '#9ca3af', backgroundColor: '#f3f4f6', padding: '2px 4px', borderRadius: '4px' }}>
                      {event.lat.toFixed(4)}, {event.lng.toFixed(4)}
                    </code>
                    <button 
                      onClick={(e) => copyToClipboard(e, `${event.lat}, ${event.lng}`)}
                      style={{ 
                        background: '#7c3aed', 
                        border: 'none', 
                        cursor: 'pointer', 
                        color: 'white', 
                        borderRadius: '4px',
                        padding: '4px 8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '10px'
                      }}
                    >
                      <Copy size={10} /> Copy
                    </button>
                  </div>

                  {/* Working External Link */}
                  {event.url ? (
                    <a 
                      href={event.url} 
                      target="_blank" 
                      rel="noreferrer" 
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        gap: '6px', 
                        marginTop: '10px', 
                        padding: '8px',
                        backgroundColor: '#7c3aed',
                        borderRadius: '6px',
                        color: 'white', 
                        textDecoration: 'none', 
                        fontWeight: 'bold',
                        fontSize: '12px'
                      }}
                    >
                      Visit Event Site <ExternalLink size={12} />
                    </a>
                  ) : (
                    <div style={{ marginTop: '10px', fontSize: '10px', color: '#ef4444', fontStyle: 'italic' }}>
                      No URL available for this event
                    </div>
                  )}
                </div>
              </Popup>
            )}
          </React.Fragment>
        ))}
      </Map>
    </div>
  );
}

export default MapView;