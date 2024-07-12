# prompt-iteration
Compares the two most recent prompt/response pairs and highlights their differences.
If given a "right answer," also shows how similar the current response is to the right answer.

Currently only supports models on Alibaba's Dashscope platform.

## Project setup

1. Clone the repository:
    ```
   git clone https://github.com/hugo2f/prompt-iteration.git
   cd prompt-iteration
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate venv:
   - On macOS and Linux:
      ```
      source venv/bin/activate
      ```
     
   - On Windows:
      ```
      venv\Scripts\activate
      ```

4. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Setup environment variables:
   ```
   cp .env.example .env
   ```
   In `.env`, Copy your dashscope API key under `DASHSCOPE_API_KEY`

## Running the app
To run the project:
```
streamlit run src/app.py
```

## Specific uses

### Extracting JSON

If the goal is to get a response containing the right `` ```json `` data, when given a
correct answer, responses will be analyzed in terms of the number of matching key/value pairs.

For image information extraction, save the image in the `images` folder,
and change the `image_name` at the beginning of `app.py`. 
