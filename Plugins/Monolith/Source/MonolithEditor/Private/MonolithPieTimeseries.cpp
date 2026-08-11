#include "MonolithPieTimeseries.h"
#include "MonolithEditorActions.h"
#include "MonolithParamSchema.h"

#include "Dom/JsonObject.h"

DEFINE_LOG_CATEGORY_STATIC(LogMonolithPieTimeseries, Log, All);

void FMonolithPieTimeseries::RegisterActions(FMonolithToolRegistry& Registry)
{
	// Registered under the "animation" namespace string (see header). MonolithEditor owns
	// the PIE-session machinery the handler delegates into.
	Registry.RegisterAction(TEXT("animation"), TEXT("sample_pie_timeseries"),
		TEXT("Start an ASYNC time-series PIE sampling session and RETURN IMMEDIATELY. Same lifecycle as run_pie_smoke: "
		     "returns {session_id, status:'running'}; poll the accumulating series + provocation fire log with poll_pie_smoke; "
		     "force-end with stop_pie_smoke. The editor's REAL frame loop advances PIE over real frames, sampling the resolved "
		     "target's 'variables' (dotted UDS-friendly member paths, e.g. 'CharacterProperties.OrientationIntent') each tick "
		     "(gated by sample_interval, capped by max_samples), and firing typed 'provocations' once each when session-elapsed "
		     "crosses their time. Resolve the target with actor (exact label) / pawn_class (class-name substring) / object_name; "
		     "optionally hop to a component_name, or set anim_instance=true to read the skeletal mesh's anim instance. "
		     "Provocations: set_control_rotation {pitch,yaw,roll}; add_movement_input {direction:[x,y,z], scale}; jump (target must "
		     "be a Character); console_command {command}. MUTATES LIVE PIE STATE via the provocations. Poll returns the full "
		     "per-sample [{t, vars:{...}}] under 'timeseries' (on completion / include_samples) and the fire log under 'provocations'."),
		FMonolithActionHandler::CreateStatic(&HandleSamplePieTimeseries),
		FParamSchemaBuilder()
			.Optional(TEXT("actor"), TEXT("string"), TEXT("Exact editor (Outliner) label of the target actor."))
			.Optional(TEXT("pawn_class"), TEXT("string"), TEXT("Substring of the target actor's class name (first match wins)."))
			.Optional(TEXT("object_name"), TEXT("string"), TEXT("Exact object name of the target actor. One of actor/pawn_class/object_name is required."))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("Component on the resolved actor to read from instead of the actor itself."))
			.Optional(TEXT("anim_instance"), TEXT("bool"), TEXT("If true, read from the (named or first) skeletal mesh component's active anim instance."), TEXT("false"))
			.Required(TEXT("variables"), TEXT("array"), TEXT("Dotted member paths sampled each tick (e.g. ['RootTransform.Rotation.Yaw','CharacterProperties.OrientationIntent']). UDS members resolve by friendly name; struct-member traversal only."))
			.OptionalAssetPath(TEXT("map"), TEXT("Level asset path to load before PIE (e.g. /Game/Tests/Monolith/Maps/M_Harness). Omit to use the current editor level."))
			.Optional(TEXT("duration_seconds"), TEXT("number"), TEXT("Seconds the editor loop advances PIE before the session auto-completes (clamped 0-120). Default 6."), TEXT("6"))
			.Optional(TEXT("sample_interval"), TEXT("number"), TEXT("Minimum seconds between samples. Default 0 (sample every tick)."), TEXT("0"))
			.Optional(TEXT("max_samples"), TEXT("number"), TEXT("Hard cap on accumulated samples (payload guard). Default 2048."), TEXT("2048"))
			.Optional(TEXT("provocations"), TEXT("array"), TEXT("Timed typed provocations fired ONCE each when session-elapsed crosses time: [{time:number, action:'set_control_rotation'|'add_movement_input'|'jump'|'console_command', params:{...}}]. set_control_rotation params {pitch,yaw,roll}; add_movement_input params {direction:[x,y,z], scale}; jump (no params; target must be a Character); console_command params {command}. Outcome reported under 'provocations'."))
			.Optional(TEXT("console_script"), TEXT("array"), TEXT("Console command strings run on the PIE world at start."))
			.Optional(TEXT("python_script"), TEXT("string"), TEXT("Python source run via IPythonScriptPlugin at start."))
			.Optional(TEXT("on_compile_errors"), TEXT("string"), TEXT("Policy when loaded Blueprints have unresolved compile errors: \"refuse\" (default) returns an error + the offending list and does NOT start PIE; \"suppress\" starts PIE anyway."), TEXT("refuse"))
			.Build());

	UE_LOG(LogMonolithPieTimeseries, Log, TEXT("MonolithEditor: registered sample_pie_timeseries under the 'animation' namespace"));
}

FMonolithActionResult FMonolithPieTimeseries::HandleSamplePieTimeseries(const TSharedPtr<FJsonObject>& Params)
{
	return FMonolithEditorActions::StartTimeseriesSession(Params);
}
