# studip-heatmap

This is a Flask application. Use ```wsgi.py``` as a wsgi point for running the application for example with gunicorn like

```
gunicorn --error-logfile ---reload --chdir /home/$USER/cronjobs/studip-heatmap/ --bind 127.0.0.1:XXXXX wsgi
```

Register an open port and replace XXXXX. After that copy the .htaccess file to your DocumentRoot in order to forward all requests to gunicorn. Remember to change the port there as well.
