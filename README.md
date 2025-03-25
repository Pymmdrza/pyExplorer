# Blockchain Explorer

A professional blockchain explorer web application that provides comprehensive insights into blockchain networks, with enhanced data visualization and user interaction capabilities.

## Features

- Real-time transaction tracking
- Detailed block information
- Address history and balance tracking
- Transaction receipt generation
- Export data in multiple formats (JSON, CSV)
- Responsive Material UI-inspired design
- Real-time data updates via WebSocket

## Quick Start

### Local Installation

```bash
# Install the blockchain explorer
pip install pyexplorer

# Install required dependencies
pyexplorer install local

# Run the application
pyexplorer run local
```

The application will be available at `http://localhost:5000`

### Docker Installation

```bash
# Install the blockchain explorer
pip install blockchain-explorer

# Install Docker dependencies and setup
pyexplorer install docker

# Run using Docker
pyexplorer run docker
```

## Configuration

The application uses a `config.json` file for API endpoints and other settings. You can modify this file to change the blockchain nodes and APIs used by the application.

## Development

To set up the development environment:

```bash
git clone https://github.com/Pymmdrza/pyExplorer
cd pyExplorer
pip install -e .
```

## CLI Commands

### Installation
- `pyexplorer install local`: Install all required dependencies for local deployment
- `pyexplorer install docker`: Setup Docker environment and install dependencies

### Running
- `pyexplorer run local`: Run the application locally
- `pyexplorer run docker`: Run the application using Docker

## License

This project is licensed under the MIT License - see the LICENSE file for details.