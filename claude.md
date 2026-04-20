# CdE Macroeconomic Dashboard

## Project Overview

A dashboard application for visualizing publicly available macroeconomic data. The dashboard will aggregate and display economic indicators from multiple authoritative sources.

## Data Sources

- **INE** (Instituto Nacional de Estadística) - Spanish national statistics
- **Eurostat** - European Union statistics
- **Yahoo Finance** - Financial market data
- **FRED** (Federal Reserve Economic Data) - US economic data
- **Other public APIs** as needed

## Project Status

**Current Phase:** Initial setup

## Ground Rules

### File Management
- **Always delete temporary files at the end of each task.** This includes any `tmp/`, `temp/`, cache files, or intermediate processing files created during development or data processing.

### Code Standards
- Write clean, maintainable code with clear variable names
- Include comments for complex logic
- Handle API errors gracefully with appropriate fallbacks

### Data Handling
- Cache API responses appropriately to avoid rate limiting
- Document data update frequencies
- Validate data before visualization

### Version Control
- Commit changes with descriptive messages
- Keep commits focused and atomic

## Directory Structure

```
CdE-Dashboard-v1/
├── claude.md          # Project documentation and rules
├── src/               # Source code
├── data/              # Cached/processed data (gitignored)
├── config/            # Configuration files
└── docs/              # Additional documentation
```

## Notes

- This project is maintained by Círculo de Empresarios
- Dashboard should be accessible and easy to interpret for economic analysis
