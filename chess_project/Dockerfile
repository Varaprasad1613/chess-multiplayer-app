FROM python:3.12.6
COPY requirements.txt ./
RUN pip3 install --user -r requirements.txt
RUN apt update && apt install -y redis-server && apt clean
COPY . ./
RUN chmod +x docker_run_server.sh
EXPOSE 80
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["./docker_run_server.sh"]


# FROM python:3.12.6

# # Set working directory
# WORKDIR /app

# # Copy and install dependencies
# COPY requirements.txt .
# RUN pip3 install --no-cache-dir -r requirements.txt

# # Copy the rest of the application code
# COPY . .

# # Make the server script executable
# RUN chmod +x docker_run_server.sh

# # Expose the correct port
# EXPOSE 8001

# # Set environment variable
# ENV PYTHONUNBUFFERED=1

# # Define the entrypoint
# ENTRYPOINT ["./docker_run_server.sh"]

