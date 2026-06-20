# use a slim Python base image
FROM python:3.11-slim

# set working directory inside container
WORKDIR /app

# copy requirements first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the project
COPY . .

# create data directories so they exist inside the container
RUN mkdir -p data/sample_jobs

# expose the port FastAPI will run on
EXPOSE 8000

# start the FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]