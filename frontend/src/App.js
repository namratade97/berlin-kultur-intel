import { useState } from 'react';
import { ApolloClient, InMemoryCache, gql, useLazyQuery } from '@apollo/client';
import MapView from './Map';
import Sidebar from './Sidebar';

// Connecting to the Python FastAPI Backend
const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql',
  cache: new InMemoryCache(),
});

const ASK_AGENT = gql`
  query AskAgent($question: String!) {
    askAgent(question: $question) {
      answer
      matches {
        eventName
        venueName    
        summary
        lat
        lng
        url
        collection
        district
      }
    }
  }
`;

function App() {
  const [events, setEvents] = useState([]);
  const [agentAnswer, setAgentAnswer] = useState("");

  const [askAgent, { loading }] = useLazyQuery(ASK_AGENT, {
    client,
    onCompleted: (data) => {
      setEvents(data.askAgent.matches); // Updating pins on map
      setAgentAnswer(data.askAgent.answer); // Updating text box
    },
  });

  return (
  <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
    <Sidebar 
      onSearch={(q) => askAgent({ variables: { question: q } })} 
      answer={agentAnswer}
      events={events}
      loading={loading}
    />
    <MapView events={events} />
  </div>
);
}

export default App;