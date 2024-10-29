# Life Tracker

A command-line tool for tracking and analyzing personal metrics across different life categories (health, wealth, relationships, etc.).

## Features

- Multi-user support with secure login
- Custom metric creation and management
- Flexible data entry with support for:
  - Quantitative metrics (numbers)
  - Qualitative metrics (ratings)
- Data visualization and analysis:
  - Single metric trends
  - Correlation analysis between metrics
- Support for both default and custom metric sets
- Historical data entry
- Detailed descriptions and examples for each metric

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd life-tracker
```

2. Install required packages:
```bash
pip3 install pandas matplotlib
```

## Usage

Run the program:
```bash
python3 life_tracker.py
```

First-time users will be prompted to:
1. Create an account
2. Choose between default metrics or create custom metrics
3. Start tracking their data

### Available Commands

- Enter daily data
- View metric correlations
- Visualize metric trends
- Manage metrics (add/edit/delete)
- Enter historical data

## Development

This project uses:
- SQLite for data storage
- Pandas for data analysis
- Matplotlib for visualization

## Future Enhancements

- Data export functionality
- Natural language processing for voice input
- Web interface
- Mobile app integration