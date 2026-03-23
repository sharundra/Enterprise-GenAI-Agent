# 1. Start with a lightweight Python 3.11 image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy ALL your project files (Python scripts, SQLite DB, PDFs) into the container
COPY . .

# 5. Expose port 8000 for FastAPI
EXPOSE 8000

# 6. The command to start the FastAPI server when the container turns on
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]