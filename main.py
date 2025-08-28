from src.nba_synth import synthesize_quarters
from src.nba_synth.features import analyze_features
from src.nba_synth.conjectures import generate_conjectures

import pandas as pd
import numpy as np
import sys
import questionary
import pyfiglet
from rich.console import Console
import utils 

console = Console()


def main_menu():
    # Automatically create a backup when the app starts.
    # create_backup(console)
    
    while True:
        title_text = pyfiglet.figlet_format("NBA Insights", font="slant")
        console.print(title_text, style="bold cyan")
        choice = questionary.select(
            "Please select an option:",
            choices=[
                "1: View Database",
                "2: Synthesize Quarterly Stats",
                "3: Run Feature Analysis",
                "4: Generate Conjectures",
                "5: Extract Insights",
                "6: Exit",
            ],
            style=utils.custom_style,
        ).ask()

        # Extract the numeric option from the choice
        try:
            option = int(choice.split(":")[0])
        except (ValueError, IndexError):
            console.print("[red]Invalid option format.[/red]")
            continue

        if option == 1:
            database = questionary.select(
                "Which dataset do you want to view?",
                choices=[
                    "Original games dataset",
                    "Synthetic quarterly stats dataset"
                ],
                style=utils.custom_style,
            ).ask()
            
            if database == "Original games dataset":
                df = pd.read_csv("data/games.csv")
                print("Original games dataset selected.")
            else:
                try:
                    df = pd.read_csv("data/synthetic_quarters.csv")
                    print("Synthetic quarterly stats dataset selected.")
                except FileNotFoundError:
                    console.print("[red]Synthetic quarterly stats dataset not found. Please generate it first.[/red]")
                    continue
            
            console.print(df.head())  # Display the first few rows of the DataFrame
            console.print(df.describe())  # Display summary statistics
            console.print(df.info())  # Display DataFrame info
            
        elif option == 2:
            df = pd.read_csv("data/games.csv")
            print("Generating synthetic quarterly stats from original games dataset...")
            
            df_synth = synthesize_quarters(df)
            df_synth.to_csv("data/synthetic_quarters.csv", index=False)
            console.print("Synthetic quarterly stats generated and saved to data/synthetic_quarters.csv")

        elif option == 3:
            database = questionary.select(
                "Which dataset do you want to analyze?",
                choices=[
                    "Original games dataset",
                    "Synthetic quarterly stats dataset"
                ],
                style=utils.custom_style,
            ).ask()
            
            if database == "Original games dataset":
                df = pd.read_csv("data/games.csv")
                print("Original games dataset selected.")
                
                # remove columns with NaN values
                df = df.dropna(axis=1)
                
                feats = [col for col in df.select_dtypes(include=['number']).columns if col not in ['season_id', 'game_id']]
                
                k = questionary.text(
                    "How many features do you want to want to project onto?",
                    style=utils.custom_style,
                ).ask()
                
                k = int(k) if k.isdigit() else None
                
                if k and k > 0:
                    df_analyzed = analyze_features(df[feats], n_clusters = k)
                    print(f'{k} features selected:', df_analyzed.columns.tolist())
                    
                    # save analyzed features to csv
                    df_analyzed.to_csv("data/analyzed_features.csv", index=False)
                    console.print(f"Feature analysis complete. Analyzed features saved to data/analyzed_features.csv")
                else:
                    console.print("[red]Invalid input. Please enter an integer.[/red]")
                    continue
            else:
                try:
                    df = pd.read_csv("data/synthetic_quarters.csv")
                    print("Synthetic quarterly stats dataset selected.")
                    
                    # remove columns with NaN values
                    df = df.dropna(axis=1)
                    
                    which_features = questionary.select(
                        "Which features do you want to analyze?",
                        choices=[
                            "All numeric features",
                            "Only first half (Q1, Q2) features"
                        ],
                        style=utils.custom_style,
                    ).ask()
                    if which_features == "All numeric features":
                        feats = [ncol for ncol in df.select_dtypes(include=['number']).columns if ncol not in ['season_id', 'game_id']]
                    if which_features == "Only first half (Q1, Q2) features":
                        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                        feats = [col for col in numeric_cols if 'Q3' not in col and 'Q4' not in col]
                    
                    k = questionary.text(
                        "How many features do you want to want to project onto?",
                        style=utils.custom_style,
                    ).ask()
                    k = int(k) if k.isdigit() else None
                    if k and k > 0:
                        df_analyzed = analyze_features(df[feats], n_clusters = k)
                        print(f'{k} features selected:', df_analyzed.columns.tolist())
                        
                        # save analyzed features to csv
                        df_analyzed.to_csv("data/synthetic_analyzed_features.csv", index=False)
                        console.print(f"Feature analysis complete. Analyzed features saved to data/synthetic_analyzed_features.csv")
                    else:
                        console.print("[red]Invalid input. Please enter an integer.[/red]")
                        continue
            
                except FileNotFoundError:
                    console.print("[red]Synthetic quarterly stats dataset not found. Please generate it first.[/red]")
                    continue
                
        elif option == 4:
            database = questionary.select(
                "Which dataset do you want to use for conjecture generation?",
                choices=[
                    "Original games dataset",
                    "Synthetic quarterly stats dataset",
                    "Analyzed features from original games dataset",
                    "Analyzed features from synthetic quarterly stats dataset"
                ],
                style=utils.custom_style,
            ).ask()
            
            if database == "Original games dataset":
                df = pd.read_csv("data/games.csv")
                print("Original games dataset selected.")
            
            if database == "Synthetic quarterly stats dataset":
                try:
                    df = pd.read_csv("data/synthetic_quarters.csv")
                    print("Synthetic quarterly stats dataset selected.")
                except FileNotFoundError:
                    console.print("[red]Synthetic quarterly stats dataset not found. Please generate it first.[/red]")
                    continue
            
            if database == "Analyzed features from original games dataset":
                try:
                    df = pd.read_csv("data/analyzed_features.csv")
                    print("Analyzed features from original games dataset selected.")
                except FileNotFoundError:
                    console.print("[red]Analyzed features from original games dataset not found. Please run feature analysis first.[/red]")
                    continue
            
            if database == "Analyzed features from synthetic quarterly stats dataset":
                try:
                    df = pd.read_csv("data/synthetic_analyzed_features.csv")
                    print("Analyzed features from synthetic quarterly stats dataset selected.")
                except FileNotFoundError:
                    console.print("[red]Analyzed features from synthetic quarterly stats dataset not found. Please run feature analysis first.[/red]")
                    continue
            
            # remove columns with NaN values
            df = df.dropna(axis=1)
                
            features = [col for col in df.select_dtypes(include=['number']).columns if col not in ['season_id', 'game_id']]
            boolean_cols = df.select_dtypes(include=['bool']).columns.tolist()
            
            target_type = questionary.select(
                "What type of target variable do you want?",
                choices=[ "Randomly select one of the features as target",
                          "Specify a target feature"],
                style=utils.custom_style,
            ).ask()
            
            if target_type == "Specify a target feature":
                target = questionary.select(
                    "Select the target feature:",
                    choices=features,
                    style=utils.custom_style,
                ).ask()
                if target not in features:
                    console.print("[red]Invalid feature selected.[/red]")
                    continue
            else:
                # choose one of the featurs to be the target randomly  
                import random
                target = random.choice(features)
                console.print("Target feature:", target)

            # ensure target is not in features
            features.remove(target)

            # conjecture on those features
            conjectures = generate_conjectures(df, features, target, boolean_cols)

            console.print(len(conjectures), "conjectures generated:")

            for conj in conjectures[:10]: # print first 10 conjectures
                console.print(conj)
                
        elif option == 5:
            console.print("[bold green]WORK IN PROGRESS: extracting insights...[/bold green]")
            
        elif option == 6:
            console.print("[bold red]Exiting. Goodbye![/bold red]")
            sys.exit(0)
        else:
            console.print("[red]Invalid option. Please choose a valid option.[/red]")

if __name__ == "__main__":
    main_menu()
    