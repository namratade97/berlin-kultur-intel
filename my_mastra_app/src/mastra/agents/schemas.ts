import { z } from 'zod';

// This is our 'Cultural Dossier' - the strict format our AI must follow.
export const CultureDossierSchema = z.object({
  eventName: z.string().describe("Name of the event or exhibition"),
  venueName: z.string().describe("The Berlin venue where this happens"),
  district: z.enum(["Mitte", "Kreuzberg", "Neukölln", "Friedrichshain", "Charlottenburg", "Other"]),
  vibeProfile: z.array(z.string()).describe("Tags like 'dark techno', 'experimental art', 'community'"),
  influenceScore: z.number().min(0).max(100).describe("How much this event impacts Berlin's culture (0-100 scale)"),
  confidenceScore: z.number().min(0).max(10).describe("AI's certainty based on available data (0-10 scale)"),
  summary: z.string().describe("A 2-sentence executive summary for the dashboard"),
});

export type CultureDossier = z.infer<typeof CultureDossierSchema>;