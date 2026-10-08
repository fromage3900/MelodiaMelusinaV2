// Pi 1.x project-local, read-only Melodia AIRI diagnostic extension.
// Does not create an Unreal writer or expose arbitrary HTTP, shell or editor verbs.
import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { readAiriBridgeHealth } from "../../Tools/AIRI/MelodiaBridge/pi_health.mjs";

export default function (pi: ExtensionAPI) {
  pi.registerTool(defineTool({
    name: "melodia_airi_health",
    label: "Melodia AIRI health",
    description: "Read a bounded health snapshot from the existing local Melodia AIRI relay. No gameplay or editor actions.",
    parameters: Type.Object({}),
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
    async execute(_toolCallId, _params, signal) {
      const snapshot = await readAiriBridgeHealth({ signal });
      return {
        content: [{ type: "text", text: JSON.stringify(snapshot) }],
        details: snapshot,
      };
    },
  }));
}
