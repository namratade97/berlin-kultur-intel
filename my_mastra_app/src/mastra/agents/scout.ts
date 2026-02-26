import 'dotenv/config';
import { Agent } from '@mastra/core/agent';
import { scraperTool } from '../tools/scraper';
import { createOpenAICompatible } from '@ai-sdk/openai-compatible';
import { z } from 'zod';

export const eventSchema = z.object({
  eventName: z.string(),
  venueName: z.string(),
  district: z.string(),
  vibeProfile: z.array(z.string()),
  influenceScore: z.number(),
  confidenceScore: z.number(),
  summary: z.string(),
});

const gateway = createOpenAICompatible({
  name: 'litellm-gateway',
  baseURL: 'http://localhost:4000/v1',
  apiKey: 'sk-1234', 
});

/**
 * Berlin Cultural Scout Agent
 * Specialized in extracting event metadata and "vibe" context.
 */
export const scoutAgent = new Agent({
  id: 'berlin-scout',
  name: 'Berlin Cultural Scout',
  instructions: `
    ## PERSONA
    You are a professional researcher. Your goal is to extract event data into valid JSON.

    ## STEP-BY-STEP PROCESS
    1. Use the 'web-scraper' tool to get the text from the provided URL.
    2. Read the text carefully.
    3. Output the result in the following JSON format.

    ## RULES
    - Do not provide a preamble (no "Here is the data").
    - Ensure vibeProfile is an array of strings.
    - summary must be under 20 words.
    - OUTPUT ONLY A SINGLE JSON OBJECT.
    - Use double quotes for all keys and string values.
    - If data is missing, use "" or 0.

    ## OUTPUT FORMAT
    ONLY RETURN RAW JSON.
    Return exactly this structure and nothing else:
    {
      "eventName": "...",
      "venueName": "...",
      "district": "...",
      "vibeProfile": [],
      "influenceScore": 0,
      "confidenceScore": 0,
      "summary": "MAX 20 WORDS."
    }
    
  `,
  model: gateway.chatModel('berlin-scout-model'),
  tools: {
    'web-scraper': scraperTool,
  },
});