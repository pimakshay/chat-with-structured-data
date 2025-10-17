import matplotlib.pyplot as plt
import matplotlib
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Use non-interactive backend for server environments
matplotlib.use('Agg')

class SimplePlotter:
    """Simple and modular plotting system for SQL agent visualizations."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize the plotter with output directory."""
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _get_project_dir(self, project_uuid: str) -> str:
        """Get or create project-specific directory."""
        project_dir = os.path.join(self.output_dir, project_uuid)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir
    
    def _save_plot(self, project_uuid: str, filename: str, fig) -> str:
        """Save plot to project directory and return the file path."""
        project_dir = self._get_project_dir(project_uuid)
        filepath = os.path.join(project_dir, filename)
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close(fig)  # Close figure to free memory
        return filepath
    
    def create_bar_chart(self, data: Dict[str, Any], project_uuid: str, query: str) -> Optional[str]:
        """Create and save a bar chart."""
        try:
            # Handle nested data structure
            if 'formatted_data_for_visualization' in data:
                data = data['formatted_data_for_visualization']
            
            labels = data.get('labels', [])
            values_data = data.get('values', [])
            
            if not labels or not values_data:
                print("No data available for bar chart")
                return None
            
            # Extract values from the first series
            values = values_data[0].get('data', []) if values_data else []
            series_label = values_data[0].get('label', 'Data') if values_data else 'Data'
            
            if not values:
                print("No values available for bar chart")
                return None
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(labels, values, color='skyblue', edgecolor='navy', alpha=0.7)
            
            # Customize the plot
            ax.set_title(f'Analysis: {query[:50]}{"..." if len(query) > 50 else ""}', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Categories', fontsize=12)
            ax.set_ylabel(series_label, fontsize=12)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value}', ha='center', va='bottom', fontweight='bold')
            
            # Rotate x-axis labels if they're long
            if any(len(label) > 10 for label in labels):
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Save the plot
            filename = f"bar_chart_{len(os.listdir(self._get_project_dir(project_uuid)))}.png"
            return self._save_plot(project_uuid, filename, fig)
            
        except Exception as e:
            print(f"Error creating bar chart: {e}")
            return None
    
    def create_line_chart(self, data: Dict[str, Any], project_uuid: str, query: str) -> Optional[str]:
        """Create and save a line chart."""
        try:
            # Handle nested data structure
            if 'formatted_data_for_visualization' in data:
                data = data['formatted_data_for_visualization']
            
            labels = data.get('labels', [])
            values_data = data.get('values', [])
            
            if not labels or not values_data:
                print("No data available for line chart")
                return None
            
            # Extract values from the first series
            values = values_data[0].get('data', []) if values_data else []
            series_label = values_data[0].get('label', 'Data') if values_data else 'Data'
            
            if not values:
                print("No values available for line chart")
                return None
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(labels, values, marker='o', linewidth=2, markersize=6, color='blue')
            
            # Customize the plot
            ax.set_title(f'Analysis: {query[:50]}{"..." if len(query) > 50 else ""}', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Categories', fontsize=12)
            ax.set_ylabel(series_label, fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Rotate x-axis labels if they're long
            if any(len(str(label)) > 10 for label in labels):
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Save the plot
            filename = f"line_chart_{len(os.listdir(self._get_project_dir(project_uuid)))}.png"
            return self._save_plot(project_uuid, filename, fig)
            
        except Exception as e:
            print(f"Error creating line chart: {e}")
            return None
    
    def create_pie_chart(self, data: Dict[str, Any], project_uuid: str, query: str) -> Optional[str]:
        """Create and save a pie chart."""
        try:
            # Handle nested data structure
            if 'formatted_data_for_visualization' in data:
                data = data['formatted_data_for_visualization']
            
            # Handle different data structures for pie charts
            if isinstance(data, list):
                # Direct list format: [{"label": "...", "value": ...}, ...]
                labels = [item.get('label', '') for item in data]
                values = [item.get('value', 0) for item in data]
            else:
                # Standard format: {"labels": [...], "values": [{"data": [...]}]}
                labels = data.get('labels', [])
                values_data = data.get('values', [])
                
                if not labels or not values_data:
                    print("No data available for pie chart")
                    return None
                
                # Extract values from the first series
                values = values_data[0].get('data', []) if values_data else []
            
            if not labels or not values:
                print("No data available for pie chart")
                return None
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = plt.cm.Set3(range(len(labels)))
            
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                             colors=colors, startangle=90)
            
            # Customize the plot
            ax.set_title(f'Analysis: {query[:50]}{"..." if len(query) > 50 else ""}', 
                        fontsize=14, fontweight='bold', pad=20)
            
            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
            
            plt.tight_layout()
            
            # Save the plot
            filename = f"pie_chart_{len(os.listdir(self._get_project_dir(project_uuid)))}.png"
            return self._save_plot(project_uuid, filename, fig)
            
        except Exception as e:
            print(f"Error creating pie chart: {e}")
            return None
    
    def create_scatter_plot(self, data: Dict[str, Any], project_uuid: str, query: str) -> Optional[str]:
        """Create and save a scatter plot."""
        try:
            # Handle nested data structure
            if 'formatted_data_for_visualization' in data:
                data = data['formatted_data_for_visualization']
            
            labels = data.get('labels', [])
            values_data = data.get('values', [])
            
            if not labels or not values_data:
                print("No data available for scatter plot")
                return None
            
            # Extract values from the first series
            values = values_data[0].get('data', []) if values_data else []
            series_label = values_data[0].get('label', 'Data') if values_data else 'Data'
            
            if not values:
                print("No values available for scatter plot")
                return None
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(labels, values, s=100, alpha=0.7, color='red', edgecolors='black')
            
            # Customize the plot
            ax.set_title(f'Analysis: {query[:50]}{"..." if len(query) > 50 else ""}', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Categories', fontsize=12)
            ax.set_ylabel(series_label, fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Rotate x-axis labels if they're long
            if any(len(str(label)) > 10 for label in labels):
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Save the plot
            filename = f"scatter_plot_{len(os.listdir(self._get_project_dir(project_uuid)))}.png"
            return self._save_plot(project_uuid, filename, fig)
            
        except Exception as e:
            print(f"Error creating scatter plot: {e}")
            return None
    
    def create_plot(self, visualization_type: str, data: Dict[str, Any], 
                   project_uuid: str, query: str) -> Optional[str]:
        """Create a plot based on the visualization type."""
        if not data or not project_uuid or not query:
            print("Missing required parameters for plotting")
            return None
        
        # Map visualization types to methods
        plot_methods = {
            'bar': self.create_bar_chart,
            'line': self.create_line_chart,
            'pie': self.create_pie_chart,
            'scatter': self.create_scatter_plot
        }
        
        plot_method = plot_methods.get(visualization_type.lower())
        if not plot_method:
            print(f"Unsupported visualization type: {visualization_type}")
            return None
        
        print(f"Creating {visualization_type} chart for project {project_uuid}")
        return plot_method(data, project_uuid, query)
