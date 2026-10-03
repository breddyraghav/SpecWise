# SpecWise

SpecWise is a product recommendation system that helps users find a suitable laptop, smartphone, or bike based on their requirements and budget.

## Live Website

https://specwise.streamlit.app/

## What it does

The user enters their requirements and SpecWise compares them with the products available in its database. It then gives a recommendation along with a match score and reasons for the recommendation.

## Categories

- Laptops
- Smartphones
- Bikes

## How it works

1. Select a product category.
2. Enter your budget and requirements.
3. SpecWise filters products based on the mandatory requirements.
4. The remaining products are scored according to the user's preferences.
5. The products are sorted by their score.
6. The best matches are displayed.

## Technologies Used

- Python
- Streamlit
- JSON
- Git
- GitHub

## Project Structure

```text
SpecWise/
├── app.py
├── README.md
├── requirements.txt
├── assets/
│   └── logo.png
├── data/
│   └── products.json
└── src/
    └── main.py