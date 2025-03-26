# Blockchain Explorer

A professional blockchain explorer web application that provides comprehensive insights into blockchain networks, with enhanced data visualization and user interaction capabilities.

![pyExplorer](https://raw.githubusercontent.com/Pymmdrza/pyExplorer/refs/heads/main/.github/index_screen-optimize.png 'pyExplorer Bitcoin block transaction and address monitoring')

## Features

- Real-time transaction tracking
- Detailed block information
- Address history and balance tracking
- Transaction receipt generation
- Export data in multiple formats (JSON, CSV)
- Responsive Material UI-inspired design
- Real-time data updates via WebSocket

## Screenshot

- Home Page ( [Screenshot](https://raw.githubusercontent.com/Pymmdrza/pyExplorer/refs/heads/main/.github/index_screen.png) )
- Transaction Page ( [Screenshot](https://raw.githubusercontent.com/Pymmdrza/pyExplorer/refs/heads/main/.github/transaction_screen.png) )
- Address Page ( [Screenshot](https://raw.githubusercontent.com/Pymmdrza/pyExplorer/refs/heads/main/.github/address_screen.png) )
- Block Page ( [Screenshot](https://raw.githubusercontent.com/Pymmdrza/pyExplorer/refs/heads/main/.github/block_screen.png) )

## Quick Start

### Docker

```
docker pull pymmdrza/pyexplorer:latest
docker run -d -p 5000:5000 --name pyexplorer pymmdrza/pyexplorer:latest
```

### Local Installation

```bash
# Install the blockchain explorer
pip install blockExplorer

# Install required dependencies
blockExplorer install local

# Run the application
blockExplorer run local
```

The application will be available at `http://localhost:5000`

### Docker Installation

```bash
# Install the blockchain explorer
pip install blockExplorer

# Install Docker dependencies and setup
blockExplorer install docker

# Run using Docker
blockExplorer run docker
```

## Configuration

The application uses a `config.json` file for API endpoints and other settings. You can modify this file to change the blockchain nodes and APIs used by the application.

## Development

To set up the development environment:

```bash
git clone https://github.com/Pymmdrza/pyExplorer
cd blockExplorer
pip install -e .
```

## CLI Commands

### Installation
- `blockExplorer install local`: Install all required dependencies for local deployment
- `blockExplorer install docker`: Setup Docker environment and install dependencies

### Running
- `blockExplorer run local`: Run the application locally
- `blockExplorer run docker`: Run the application using Docker

## License

This project is licensed under the MIT License - see the LICENSE file for details.
