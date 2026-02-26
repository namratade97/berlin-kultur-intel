import { useState } from 'react';
import { Search, Sparkles, Loader2, ExternalLink, MapPin } from 'lucide-react';

function Sidebar({ onSearch, answer, events, loading }) {
  const [input, setInput] = useState("");

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') onSearch(input);
  };

  return (
    <div style={{ 
      width: '28%', padding: '20px', backgroundColor: '#f9fafb', 
      borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column',
      height: '100vh', boxSizing: 'border-box'
    }}>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.2rem', margin: 0 }}>
        <Sparkles size={24} color="#7c3aed" /> Berlintel
      </h2>
      <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>Your one stop Berlin Kultur Agent. Ask me anything about events happening in Berlin!</p>
      
      {/* Search Input */}
      <div style={{ position: 'relative', marginTop: '20px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="I'm craving something sweet..."
          style={{ 
            width: '100%', padding: '12px 40px 12px 12px', borderRadius: '8px',
            border: '1px solid #d1d5db', outline: 'none', boxSizing: 'border-box'
          }}
        />
        <Search 
          style={{ position: 'absolute', right: '12px', top: '12px', color: '#9ca3af', cursor: 'pointer' }} 
          onClick={() => onSearch(input)}
        />
      </div>

      {/* Results Section */}
      <div style={{ marginTop: '25px', flex: 1, overflowY: 'auto', paddingRight: '5px' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6b7280', padding: '20px' }}>
            <Loader2 className="animate-spin" size={20} /> Consulting the archives...
          </div>
        ) : (
          <>
            {/* AI Text Answer */}
            {answer && (
              <div style={{ 
                padding: '15px', backgroundColor: 'white', borderRadius: '12px', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)', lineHeight: '1.5',
                border: '1px solid #e5e7eb', marginBottom: '20px', fontSize: '14px'
              }}>
                <div style={{ fontWeight: 'bold', color: '#7c3aed', marginBottom: '8px', fontSize: '12px', textTransform: 'uppercase' }}>
                  Agent Intelligence
                </div>
                {answer}
              </div>
            )}

            {!answer && !events?.length && (
            <div style={{ marginTop: '40px', padding: '0 10px' }}>
                <div style={{ 
                backgroundColor: '#f3f4f6', 
                borderRadius: '12px', 
                padding: '20px', 
                border: '1px dashed #d1d5db' 
                }}>
                <h3 style={{ fontSize: '14px', color: '#374151', margin: '0 0 10px 0' }}>
                    System Architecture
                </h3>
                <ul style={{ 
                    fontSize: '13px', 
                    color: '#6b7280', 
                    paddingLeft: '18px', 
                    lineHeight: '1.6',
                    margin: 0
                }}>
                    <li><strong>Hybrid RAG:</strong> Semantic search via <strong>Qdrant</strong> vector store.</li>
                    <li><strong>Agentic Routing & Text2SQL:</strong> Dynamic intent detection that translates natural language into <strong>executable SQL</strong> for precise historical analytics.</li>
                    <li><strong>Model Agnostic:</strong> Multi-LLM fallback (Gemini/Llama) via <strong>LiteLLM</strong>.</li>
                    <li><strong>Evaluation:</strong> Quality-gated responses via <strong>DeepEval</strong>.</li>
                </ul>
                <p style={{ 
                    fontSize: '12px', 
                    color: '#9ca3af', 
                    marginTop: '15px', 
                    fontStyle: 'italic' 
                }}>
                    Ask me about sweet food, events in Mitte, or the total count of festivals in March.
                </p>
                </div>
            </div>
            )}

            {/* Event Cards */}
            {events && events.length > 0 && (
              <div style={{ marginTop: '10px' }}>
                <h3 style={{ fontSize: '14px', color: '#4b5563', marginBottom: '12px' }}>Suggested Events:</h3>
                {events.map((event, i) => (
                  <div key={i} style={{ 
                    padding: '16px', backgroundColor: 'white', borderRadius: '12px', 
                    marginBottom: '12px', border: '1px solid #e5e7eb',
                    transition: 'transform 0.2s', borderLeft: '4px solid #7c3aed'
                  }}>
                    <h4 style={{ margin: '0 0 6px 0', fontSize: '15px' }}>{event.eventName}</h4>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#6b7280', fontSize: '12px', marginBottom: '8px' }}>
                      <MapPin size={14} />
                      <span>{event.venueName} • {event.district}</span>
                    </div>

                    <p style={{ fontSize: '13px', color: '#374151', margin: '0 0 12px 0', lineHeight: '1.4' }}>
                      {event.summary}
                    </p>

                    <a 
                    href={event.url || "#"} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    onClick={(e) => {
                        if(!event.url) e.preventDefault();
                    }}
                    style={{ 
                        display: 'inline-block',
                        marginTop: '10px',
                        padding: '8px 12px',
                        backgroundColor: '#7c3aed1a',
                        borderRadius: '6px',
                        color: '#7c3aed',
                        textDecoration: 'none',
                        fontWeight: 'bold'
                    }}
                    >
                    View Details on Official Site <ExternalLink size={12} />
                    </a>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Sidebar;