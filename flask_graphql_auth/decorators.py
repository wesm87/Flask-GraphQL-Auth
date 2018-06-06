from flask import _app_ctx_stack as ctx_stack, current_app
from .exceptions import *
from functools import wraps
import jwt


def decode_jwt(encoded_token, secret, algorithm, identity_claim_key,
               user_claims_key):
    """
    Decodes an encoded JWT

    :param encoded_token: The encoded JWT string to decode
    :param secret: Secret key used to encode the JWT
    :param algorithm: Algorithm used to encode the JWT
    :param identity_claim_key: expected key that contains the identity
    :param user_claims_key: expected key that contains the user claims
    :return: Dictionary containing contents of the JWT
    """
    # This call verifies the ext, iat, and nbf claims
    data = jwt.decode(encoded_token, secret, algorithms=[algorithm])

    # Make sure that any custom claims we expect in the token are present
    if 'jti' not in data:
        raise JWTDecodeError("Missing claim: jti")
    if identity_claim_key not in data:
        raise JWTDecodeError("Missing claim: {}".format(identity_claim_key))
    if 'type' not in data or data['type'] not in ('refresh', 'access'):
        raise JWTDecodeError("Missing or invalid claim: type")
    if user_claims_key not in data:
        data[user_claims_key] = {}

    return data


def get_jwt_data(token, token_type):
    jwt_data = decode_jwt(
        encoded_token=token,
        secret=current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256',
        identity_claim_key=current_app.config['JWT_IDENTITY_CLAIM'],
        user_claims_key=current_app.config['JWT_USER_CLAIMS']
        )

    # token type verification
    if jwt_data['type'] != token_type:
        raise WrongTokenError('Only {} tokens are allowed'.format(token_type))

    return jwt_data


def verify_jwt_in_argument(token):
    jwt_data = get_jwt_data(token, 'access')
    ctx_stack.top.jwt = jwt_data


def verify_refresh_jwt_in_argument(token):
    jwt_data = get_jwt_data(token, 'refresh')
    ctx_stack.top.jwt = jwt_data


def jwt_required(fn):
    """
    A decorator to protect a Flask endpoint.

    If you decorate an endpoint with this, it will ensure that the requester
    has a valid access token before allowing the endpoint to be called. This
    does not check the freshness of the access token.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_argument(kwargs[current_app.config['JWT_TOKEN_ARGUMENT_NAME']])
        return fn(*args, **kwargs)
    return wrapper


def jwt_refresh_token_required(fn):
    """
    A decorator to protect a Flask endpoint.

    If you decorate an endpoint with this, it will ensure that the requester
    has a valid refresh token before allowing the endpoint to be called.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_refresh_jwt_in_argument(kwargs[current_app.config['JWT_TOKEN_ARGUMENT_NAME']])
        return fn(*args, **kwargs)
    return wrapper
