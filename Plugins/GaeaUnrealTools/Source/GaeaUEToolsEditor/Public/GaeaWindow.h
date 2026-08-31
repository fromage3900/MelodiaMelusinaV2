// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "Widgets/SWindow.h"
#include "CoreMinimal.h"

/**
 * 
 */

class GAEAUETOOLSEDITOR_API SGaeaWindow : public SWindow
{

public:
	SGaeaWindow();
	virtual ~SGaeaWindow() override;
	
	SLATE_BEGIN_ARGS(SGaeaWindow)
	{
		Title(FText::GetEmpty());
		ClientSize(FVector2d(800,600));
		SizingRule(ESizingRule::FixedSize);
	}

	SLATE_ARGUMENT(FText, Title);
	SLATE_ARGUMENT(FVector2D, ClientSize);
	SLATE_ARGUMENT(ESizingRule, SizingRule);
	
	
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		SWindow::Construct(SWindow::FArguments()
			.Title(InArgs._Title)
			.ClientSize(InArgs._ClientSize)
			.SizingRule(InArgs._SizingRule));
			
	}

	
	bool bClosed = false;

	FOnWindowClosed WindowStatus;
	

protected:
	
	
	
    
	
};
    

