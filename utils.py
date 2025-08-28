from prompt_toolkit.styles import Style
from questionary import select
from rich.panel import Panel
from rich.prompt import Prompt
from pyfiglet import Figlet
import questionary

__all__ = [
    'custom_style',
    'git_custom_style',
    'convert_hypothesis',
    'keyword_map',
    'view_conjectures',
    'write_on_the_wall',
]

custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'bold'),
    ('answer', 'fg:cyan bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:cyan'),
    ('separator', 'fg:#6C6C6C'),
    ('instruction', 'fg:#a3a3a3 italic'),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])


git_custom_style = Style([
    ('qmark', 'fg:magenta bold'),
    ('question', 'bold fg:magenta'),
    ('answer', 'fg:magenta bold'),
    ('pointer', 'fg:magenta bold'),
    ('highlighted', 'fg:magenta bold'),
    ('selected', 'fg:magenta'),
    ('separator', 'fg:#6C6C6C'),
    ('instruction', 'fg:#a3a3a3 italic'),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])

def write_on_the_wall(agent, numerical_columns, target_invariants=None, search=True, console=None):
    """
    Interactively view conjectures for a target invariant.

    (docstring omitted for brevity)
    """
    conjectures = agent.conjectures
    if not conjectures:
        console.print("[yellow]No conjectures to display.[/yellow] Use the 'Make Conjectures' option to add a new conjecture.")
        return

    if console is None:
        from rich.console import Console
        console = Console()

    # Display header using Figlet.
    from pyfiglet import Figlet  # ensure Figlet is imported here if not already
    fig = Figlet(font='slant')
    console.print(fig.renderText("Polytope AI"), style="bold cyan")
    console.print("Author: Randy R. Davila, PhD")
    console.print("Automated Conjecturing since 2017")
    console.print("=" * 80)

    # <<< NEW: Define helper functions here (moved up) >>>
    def get_sharp_subset(df, sharp_ids):
        if 'name' in df.columns:
            return df[df['name'].isin(sharp_ids)]
        else:
            return df.loc[sharp_ids]

    def format_sharp_instances(instances, num_columns=4, indent="    "):
        items = sorted(str(item) for item in instances)
        if not items:
            return ""
        max_width = max(len(item) for item in items)
        rows = (len(items) + num_columns - 1) // num_columns
        formatted_rows = []
        for row in range(rows):
            row_items = []
            for col in range(num_columns):
                idx = col * rows + row
                if idx < len(items):
                    row_items.append(items[idx].ljust(max_width))
            formatted_rows.append(indent + "   ".join(row_items))
        return "\n".join(formatted_rows)

    def find_common_boolean_properties(df, sharp_ids, boolean_columns):
        subset = get_sharp_subset(df, sharp_ids)
        common_props = {}
        for col in boolean_columns:
            unique_vals = subset[col].unique()
            if len(unique_vals) == 1:
                common_props[col] = unique_vals[0]
        return common_props

    def find_common_numeric_properties(df, sharp_ids, numeric_columns):
        subset = get_sharp_subset(df, sharp_ids)
        common_props = {}
        for col in numeric_columns:
            values = subset[col].dropna()
            props = []
            if (values == 0).all():
                props.append("all zero")
            common_props[col] = props
        # Check if all properties are the same numeric value.
        for col in numeric_columns:
            values = subset[col].dropna()
            if len(values.unique()) == 1:
                common_props[col] = [f"all {values.iloc[0]}"]
        return common_props
    # <<< END OF NEW HELPER FUNCTIONS >>>

    # Use all available target invariants if none are provided.
    if target_invariants is None:
        target_invariants = list(agent.conjectures.keys())

    # Prompt for target invariant selection if more than one exists.
    # Prompt for target invariant selection if more than one exists.
    if len(target_invariants) > 1:
        selected_target = select("Select a target invariant:", choices=target_invariants).ask()
    else:
        selected_target = target_invariants[0]


    # Prompt the user to select a conjecture category.
    category_choice = select(
        "Select a conjecture category:",
        choices=["Equalities", "Upper Bounds", "Lower Bounds", "Exit"],
        style=custom_style,
    ).ask()
    if category_choice.lower().startswith("equal"):
        category_key = "equals"
    elif category_choice.lower().startswith("upper"):
        category_key = "upper"
    elif category_choice.lower().startswith("lower"):
        category_key = "lower"
    elif category_choice.lower().startswith("exit"):
        return
    else:
        console.print("[red]Invalid category selected.[/red]")
        return

    # Retrieve the list of conjectures for the selected target and category.
    conj_list = agent.conjectures.get(selected_target, {}).get(category_key, [])
    if not conj_list:
        console.print(f"[red]No {category_choice} conjectures available for target invariant {selected_target}.[/red]")
        return

    # Build a numbered list of conjecture summaries.
    choices_list = []
    for i, conj in enumerate(conj_list[:10], start=1):
        hypothesis = convert_hypothesis(conj.hypothesis)
        conclusion = conj._set_conclusion()
        statement = f"For any {hypothesis}, {conclusion}."
        summary = f"{i}: {statement}"
        choices_list.append(summary)
    choices_list.append("Exit")

    # Let the user select a conjecture summary.
    selected_summary = select("Select a conjecture to view details:", choices=choices_list, style=custom_style).ask()
    if selected_summary == "Exit":
        return

    try:
        index = int(selected_summary.split(":")[0]) - 1
    except (ValueError, IndexError):
        console.print("[red]Error processing your selection.[/red]")
        return
    selected_conj = conj_list[index]

    # --- Build detailed information ---
    details_lines = []
    hypothesis = convert_hypothesis(selected_conj.hypothesis)
    conclusion = selected_conj._set_conclusion()

    # <<< NEW: Compute an equality clause using common boolean properties >>>
    equality_clause = ""
    if (search and hasattr(agent, 'knowledge_table') and
        hasattr(selected_conj, 'sharp_instances') and selected_conj.sharp_instances):
        # Get the set of IDs (or indices) for the sharp instances.
        sharp_ids = list(selected_conj.sharp_instances)
        sharp_set = set(sharp_ids)
        if hasattr(agent, 'boolean_columns'):
            # Compute common boolean properties among sharp instances.
            common_bool_for_statement = find_common_boolean_properties(agent.knowledge_table, sharp_ids, agent.boolean_columns)
            # For each common boolean property, check if the set of rows in the entire knowledge table
            # that satisfy the property is exactly equal to the sharp instance set.
            for bool_key, bool_val in common_bool_for_statement.items():
                # We typically want to check for the property being True.
                if bool_val is True:
                    # Get the indices (or IDs) for which the boolean column is True.
                    full_set = set(agent.knowledge_table.index[agent.knowledge_table[bool_key]])
                    if full_set == sharp_set:
                        equality_clause = f" with equality if and only if {bool_key} is True"
                        break

    # <<< END OF NEW EQUALITY CLAUSE CODE >>>

    # Now, build the statement including the equality clause.
    if selected_conj.touch > 0:
        statement = f"\n For any {hypothesis}, \n  \n        {conclusion}{equality_clause}, \n  \n  and this bound is sharp on at least {selected_conj.touch} simple polytopes. \n"
    else:
        statement = f"\n For any {hypothesis}, \n  \n        {conclusion}{equality_clause}. \n"

    details_lines.append(f"[bold magenta]Statement: [bold green]{statement}")
    details_lines.append(f"[bold magenta]Target Invariant:[/bold magenta] {selected_conj.target}")
    # other invariants
    if hasattr(selected_conj, 'keywords') and selected_conj.keywords:
        for keyword in selected_conj.keywords:
            keyword = keyword.lower()
            keyword = keyword_map(keyword)
            details_lines.append(f"[bold magenta]Keyword Information:[/bold magenta] {keyword}")

    details_lines.append(f"[bold magenta]Bound Type:[/bold magenta] {selected_conj.bound_type}")
    if hasattr(selected_conj, 'complexity') and selected_conj.complexity is not None:
        details_lines.append(f"[bold magenta]Complexity:[/bold magenta] {selected_conj.complexity}")
    if selected_conj.touch > 0:
        if selected_conj.touch > 1:
            details_lines.append(f"[bold magenta]Sharp on:[/bold magenta] {selected_conj.touch} objects.")
        else:
            details_lines.append(f"[bold magenta]Sharp on:[/bold magenta] 1 object.")
    else:
        details_lines.append(f"[bold magenta]Inequality is strict.[/bold magenta]")

    # --- (The rest of your code remains unchanged) ---
    # If sharp instances exist, show them and compute common properties.
    if hasattr(selected_conj, 'sharp_instances') and selected_conj.sharp_instances:
        details_lines.append(f"[bold magenta]Sharp Instances:[/bold magenta]")
        details_lines.append(format_sharp_instances(selected_conj.sharp_instances))
        if search and hasattr(agent, 'knowledge_table'):
            sharp_ids = list(selected_conj.sharp_instances)
            common_bool = {}
            common_numeric = {}
            if hasattr(agent, 'boolean_columns'):
                boolean_columns = agent.boolean_columns
                common_bool = find_common_boolean_properties(agent.knowledge_table, sharp_ids, boolean_columns)
            if hasattr(agent, 'numerical_columns'):
                common_numeric = find_common_numeric_properties(agent.knowledge_table, sharp_ids, numerical_columns)
            if common_bool or common_numeric:
                details_lines.append(f"[bold magenta]Common properties among sharp instances:[/bold magenta]")
                if common_bool:
                    details_lines.append("[bold magenta]Constant boolean columns:[/bold magenta]")
                    for col, val in common_bool.items():
                        details_lines.append(f"   {col} == {val}")
                if common_numeric:
                    details_lines.append("[bold magenta]Common numeric properties:[/bold magenta]")
                    for col, props in common_numeric.items():
                        if props:
                            details_lines.append(f"   {col}: {', '.join(props)}")
                        else:
                            details_lines.append(f"   {col}: None")
            else:
                details_lines.append(f"[bold magenta]No common properties found among sharp instances.[/bold magenta]")

    # Optionally, include percentage info from the knowledge table.
    if search and hasattr(agent, 'knowledge_table') and selected_conj.hypothesis in agent.knowledge_table.columns:
        hyp_df = agent.knowledge_table[agent.knowledge_table[selected_conj.hypothesis] == True]
        total_hyp = len(hyp_df)
        if total_hyp > 0:
            percent_sharp = 100 * selected_conj.touch / total_hyp
            details_lines.append(f"[bold magenta]Percentage of hypothesis objects that are sharp:[/bold magenta] {percent_sharp:.1f}%")
        else:
            details_lines.append(f"[bold magenta]No objects satisfy the hypothesis.[/bold magenta]")

    details_text = "\n".join(details_lines)

    # Display the details in a Rich Panel.
    from rich.panel import Panel  # ensure Panel is imported if needed
    panel = Panel(details_text,
                  title=f"[bold magenta]{category_choice} Conjecture Details[/bold magenta]",
                  style="cyan")
    console.print(panel)

    # Wait for the user and then return to the conjecture menu.
    from rich.prompt import Prompt  # ensure Prompt is imported if needed
    Prompt.ask("Press Enter to return to the conjecture menu")
    write_on_the_wall(agent, numerical_columns, target_invariants=[selected_target], search=search, console=console)
