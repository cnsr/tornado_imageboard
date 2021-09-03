echo "Updating the project..."
source ${HOME}/.profile
pyenv local ib &&
git pull &&
pip install -r requirements.txt &&
poetry self update &&
poetry install --no-dev &&
echo "Done"
