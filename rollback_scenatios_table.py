#!/usr/bin/env python3

import re
import os

def parse_rollback_scenarios(file_path):
    """Parse the ROLLBACK_SCENARIOS.md file and extract relevant information."""
    scenarios = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split by H2 sections (each scenario)
    scenario_sections = re.split(r'\n## ', content)
    
    # Skip the first section if it doesn't start with a scenario
    if not scenario_sections[0].startswith('## '):
        scenario_sections = scenario_sections[1:]
    else:
        scenario_sections[0] = scenario_sections[0][3:]  # Remove '## ' from the first section
    
    for section in scenario_sections:
        scenario_data = {}
        
        # Get scenario name (H2)
        scenario_name = section.split('\n')[0].strip()
        scenario_data['scenario'] = scenario_name
        
        # Get module path
        module_match = re.search(r'- module: (.*?)$', section, re.MULTILINE)
        if module_match:
            scenario_data['module'] = module_match.group(1).strip()
        else:
            scenario_data['module'] = "N/A"
        
        # Get ID
        id_match = re.search(r'- id: (.*?)$', section, re.MULTILINE)
        if id_match:
            scenario_data['id'] = id_match.group(1).strip()
        else:
            scenario_data['id'] = "N/A"
        
        # Extract the entire "What" section
        what_section = re.search(r'### What\s+(.*?)(?=\n###|\Z)', section, re.DOTALL)
        if what_section:
            # Get the entire "What" section
            what_text = what_section.group(1).strip()
            # Format multi-line text to work in a markdown table cell
            # Replace line breaks with <br> tags for proper rendering in the table
            what_text = what_text.replace('\n\n', '<br><br>')
            what_text = what_text.replace('\n', '<br>')
            scenario_data['description'] = what_text
        else:
            scenario_data['description'] = "No description available"
        
        # Extract Rollback need
        rollback_need = re.search(r'- need: (.*?)$', section, re.MULTILINE)
        if rollback_need:
            scenario_data['rollback'] = rollback_need.group(1).strip()
        else:
            scenario_data['rollback'] = "N/A"
        
        # Extract Rollback resource
        rollback_resource = re.search(r'- resource: (.*?)$', section, re.MULTILINE)
        if rollback_resource:
            scenario_data['resource'] = rollback_resource.group(1).strip()
        else:
            scenario_data['resource'] = "N/A"
        
        scenarios.append(scenario_data)
    
    return scenarios

def generate_markdown_table(scenarios):
    """Generate a markdown table from the extracted scenarios data."""
    
    # Table header
    table = "# Rollback Scenarios Table\n\n"
    table += "| Scenario | Rollback | Resource | Description | Module |\n"
    table += "|----------|----------|----------|-------------|--------|\n"
    
    # Table rows
    for scenario in scenarios:
        # Create a link to the scenario in ROLLBACK_SCENARIOS.md
        scenario_link = f"[{scenario['scenario']}](ROLLBACK_SCENARIOS.md#{scenario['scenario'].lower().replace(' ', '-')})"
        module_link = f"[{os.path.basename(scenario['module'])}]({scenario['module']})"
        
        table += f"| {scenario_link} | {scenario['rollback']} | {scenario['resource']} | {scenario['description']} | {module_link} |\n"
    
    return table

def main():
    input_file = "ROLLBACK_SCENARIOS.md"
    output_file = "ROLLBACK_SCENARIOS_TABLE.md"
    
    # Parse the input file
    scenarios = parse_rollback_scenarios(input_file)
    
    # Generate the markdown table
    table = generate_markdown_table(scenarios)
    
    # Write the table to the output file
    with open(output_file, 'w') as f:
        f.write(table)
    
    print(f"Table has been written to {output_file}")

if __name__ == "__main__":
    main()