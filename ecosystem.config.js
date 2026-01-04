module.exports = {
  apps: [
    {
      name: "cloudcost-backend",
      cwd: "/var/www/cloudcost",
      script: "./backend/.venv/bin/uvicorn",
      interpreter: "none",
      args: "backend.main:app --host 0.0.0.0 --port 8000",
      env: {
        PYTHONUNBUFFERED: "1"
      }
    },
    {
      name: "cloudcost-frontend",
      script: "npm",
      args: "start",
      cwd: "./frontend",
      env: {
        PORT: "3000"
      }
    }
  ]
}
