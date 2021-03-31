# vLab Bot

Chatbot for the matrix chat of [das labor](https://das-labor.org).

## Deployment

Bot commands are realized as 
[hemppa](https://github.com/vranki/hemppa)-modules. They must 
be placed inside the `modules` folder of a running hemppa-instance.

Some modules (and hemppa itself) require environment variables. 
On startup you will see
with variables are missing. Add them to the `run.sh` script.
A good way to find places which use environment variable is
`grep 'os.environ' hemppa_modules/*`.
