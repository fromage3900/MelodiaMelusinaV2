// Copyright tumourlove. All Rights Reserved.
// MonolithUIRegistryActions.h
//
// MCP action registrations that surface the type registry / allowlist for
// diagnostic / discovery use. Lives separate from MonolithUIActions.h so the
// hot CRUD path (create_widget_blueprint, add_widget, set_widget_property)
// stays uncluttered as more registry-introspection actions land.

#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUIRegistryActions
{
public:
    /** Bulk-register all registry diagnostic actions under the `ui` namespace. */
    static void RegisterActions(FMonolithToolRegistry& Registry);

    /** `ui::dump_property_allowlist` — returns `{type, allowed_paths:[...]}`. */
    static FMonolithActionResult HandleDumpPropertyAllowlist(const TSharedPtr<FJsonObject>& Params);
};
