# ethereum-analysis-tool
Python library to extract data from go-ethereum local LevelDB for its analysis with pandas. 
## Environment set up Ubuntu 16.04
Instructions for the environment set up on an Ubuntu 16.04 virtual machine.
### Download and install the stable version of go-ethereum
```
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt-get update
sudo apt-get install ethereum
```
### Install pre-requisites for ethereum Python libraries and Solidity environment
```
sudo apt-get install libssl-dev build-essential automake pkg-config libtool libffi-dev libgmp-dev libyaml-cpp-dev solc
```
### Create a Python virtual environment
```
sudo apt-get install -y python3-dev python3-pip
pip3 install --upgrade pip
pip3 install virtualenv
virtualenv ethereum-analysis-tools
source ethereum-analysis-tools/bin/activate
```
### Download and install ethereum-analysis-tools
```
sudo apt-get install git
pip install git+https://github.com/carlesperezj/ethereum-analysis-tool.git
cd ethereum-analysis-tool
pip install -r requirements.txt
python setup.py install
```
### Install optional libraries for Pandas and Jupyter notebooks
```
sudo apt-get install pandoc
sudo apt-get install texlive-xetex
```
## Obtain a database to analyse
Execute geth on the testnet and wait for synchronisation
```
geth --rinkeby --datadir "/home/ethereum/eth-rinkeby/" &> rinkeby.log
```
## Start Jupyter
```
jupyter notebook
```
