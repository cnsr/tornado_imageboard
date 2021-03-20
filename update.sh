source ${HOME}/.profile
pyenv local ib &&
git pull &&
pip install -r requirements.txt &&
poetry install &&
echo "Done"
