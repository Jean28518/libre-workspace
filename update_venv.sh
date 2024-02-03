if [ -d "src/lac/" ]; then
    source src/lac/.env/bin/activate
else
    source .env/bin/activate
fi

# Update all pip packages
pip install --upgrade pip
pip install --upgrade -r requirements.txt