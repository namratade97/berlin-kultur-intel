import { scoutAgent } from './mastra/agents/scout';
import { CultureDossierSchema } from './mastra/agents/schemas';

async function runScout() {
  console.log("Scout is analyzing Berlin culture...");

  try {

    const result = await scoutAgent.generate(
      "Berghain is hosting a 24-hour industrial techno marathon this weekend in Friedrichshain. Expect heavy bass and a dark aesthetic."
    );

    const cleanJson = result.text.replace(/```json|```/g, "").trim();

    const rawObject = JSON.parse(cleanJson);


    const validatedData = CultureDossierSchema.parse(rawObject);

    console.log("SUCCESS! Validated Data:");
    console.dir(validatedData, { depth: null });

  } catch (error) {
    console.error("Extraction failed.");
    console.error("AI returned this instead of JSON:", error);
  }
}

runScout();