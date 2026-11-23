Contacts API
============

The API stores contacts belonging to verified accounts. Start services with
``docker compose up --build -d`` after configuring ``.env``. Swagger is served
at ``/docs``. Use the local Mailpit UI to open email verification links.

Authentication
--------------

Register with ``POST /auth/signup``, confirm email, then submit username and
password as form fields to ``POST /auth/login``. Send the returned bearer token
in the Authorization header. Reset links contain a token to submit in the JSON
body of ``POST /auth/reset-password`` together with a new password. Reset tokens
are single-use; resetting the password revokes previous access tokens.

Birthdays include today and the following six days. February 29 is celebrated
on February 28 in non-leap years. Contact search uses the ``q`` query parameter.

Only administrators can change their avatar in the final assignment. To promote
an existing verified account run ``python -m app.admin EMAIL`` inside the app
container, then sign in again. Registration cannot assign administrator rights.

Redis stores only public account fields and authorization metadata, with a
60-second TTL. Account changes invalidate cached records. The API fails closed
if Redis is unavailable. The /me limit is shared between workers.

Modules
-------

.. automodule:: app.repository
   :members:

.. automodule:: app.auth
   :members:

.. automodule:: app.contacts
   :members:

.. automodule:: app.dependencies
   :members:

.. automodule:: app.security
   :members:

.. automodule:: app.services
   :members:

.. automodule:: app.users
   :members:

.. automodule:: app.models
   :members:
   :exclude-members: Base

.. automodule:: app.schemas
   :members:
