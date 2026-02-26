import express from 'express';
import { mastra } from './mastra/index';
import { eventSchema } from './mastra/agents/scout';

const app = express();
app.use(express.json());

app.post('/scout', async (req, res) => {
  const { url } = req.body;
  
  const scout = mastra.getAgent('scoutAgent'); 

  try {
    console.log(`Mastra is scouting: ${url}`);

    const result = await scout.generate(
      `First, use the web-scraper to get content from ${url}. 
       Read the content and extract the event details.
       Provide the final result as a clean JSON object matching the schema.`, 
      {
        maxSteps: 5,
        modelSettings: {
          maxOutputTokens: 1500,
          temperature: 0,      
        }
      }
    );

    
    let rawData: any;

    if (result.text) {
      console.log("Extracting JSON from agent text...");
      const jsonMatch = result.text.match(/(\{[\s\S]*?\})/g);
      if (jsonMatch) {
        try {
            // We take the last JSON block in case there is reasoning text before it
            rawData = JSON.parse(jsonMatch[jsonMatch.length - 1]);
        } catch (e) {
            console.error("Failed to parse JSON from text block");
        }
      }
    }

    // Fallback: Check toolResults if text was empty or didn't contain JSON
    if (!rawData && result.toolResults && result.toolResults.length > 0) {
      console.log("Checking tool results for data...");
      const lastResult = result.toolResults[result.toolResults.length - 1];
      rawData = (lastResult as any).output;
    }

    // Fallback: Checking if Mastra populated .object anyway
    if (!rawData && (result as any).object) {
      rawData = (result as any).object;
    }

    if (!rawData || typeof rawData !== 'object') {
        console.error("Full Result for Debugging:", JSON.stringify(result, null, 2));
        throw new Error("Agent failed to provide a valid JSON object. Check if the scraper returned enough content.");
    }

    // MANUAL ZOD VALIDATION 
    const validatedData = eventSchema.parse(rawData);
    
    console.log("Data validated, sending to Python audit:", validatedData.eventName);

    // PYTHON LAYER HANDOFF
    const pythonResponse = await fetch('http://localhost:8000/validate-and-store', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(validatedData)
    });

    if (!pythonResponse.ok) {
        const errorText = await pythonResponse.text();
        throw new Error(`Python Audit Error: ${errorText}`);
    }

    const finalResult = await pythonResponse.json();
    res.json(finalResult);

  } catch (error: any) {
    console.error('Pipeline Error:', error.message);
    
    // If it's a Zod error, we make the output readable
    if (error.name === 'ZodError') {
      return res.status(422).json({
        error: 'Schema Validation Failed',
        details: error.errors
      });
    }

    res.status(500).json({ 
      error: 'Processing failed', 
      details: error.message 
    });
  }
});

const server = app.listen(3000, () => {
  console.log('Mastra Signal Processor on port 3000 ...');
});

server.timeout = 600000;