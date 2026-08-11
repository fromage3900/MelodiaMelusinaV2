#pragma once

#include "MonolithAIInternal.h"

class FMonolithAIEQSActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// EQS CRUD
	static FMonolithActionResult HandleCreateEQSQuery(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetEQSQuery(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListEQSQueries(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDeleteEQSQuery(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateEQSQuery(const TSharedPtr<FJsonObject>& Params);

	// Generators
	static FMonolithActionResult HandleAddEQSGenerator(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveEQSGenerator(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureEQSGenerator(const TSharedPtr<FJsonObject>& Params);

	// Tests
	static FMonolithActionResult HandleAddEQSTest(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveEQSTest(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureEQSTest(const TSharedPtr<FJsonObject>& Params);

	// Scoring & Filter
	static FMonolithActionResult HandleConfigureEQSScoring(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureEQSFilter(const TSharedPtr<FJsonObject>& Params);

	// Type enumeration
	static FMonolithActionResult HandleListEQSGeneratorTypes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListEQSTestTypes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListEQSContexts(const TSharedPtr<FJsonObject>& Params);

	// Validation
	static FMonolithActionResult HandleValidateEQSQuery(const TSharedPtr<FJsonObject>& Params);

	// Spec builder & templates
	static FMonolithActionResult HandleBuildEQSQueryFromSpec(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleReorderEQSTests(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCreateEQSFromTemplate(const TSharedPtr<FJsonObject>& Params);
};
