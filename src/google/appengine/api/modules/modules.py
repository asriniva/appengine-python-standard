#!/usr/bin/env python
#
# Copyright 2007 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Exposes methods to control services (modules) and versions of an app.

Services were formerly known as modules and the API methods still
reflect that naming. For more information and code samples, see
`Using the Modules API
<https://cloud.google.com/appengine/docs/standard/python/using-the-modules-api>`_.
"""

__all__ = [
    'Error',
    'InvalidModuleError',
    'InvalidVersionError',
    'InvalidInstancesError',
    'UnexpectedStateError',
    'TransientError',

    'get_current_module_name',
    'get_current_version_name',
    'get_current_instance_id',
    'get_modules',
    'get_versions',
    'get_default_version',
    'get_num_instances',
    'set_num_instances',
    'set_num_instances_async',
    'start_version',
    'start_version_async',
    'stop_version',
    'stop_version_async',
    'get_hostname']


import logging
import os

import six

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.modules import modules_service_pb2
from google.appengine.runtime import apiproxy_errors


class Error(Exception):
  """Base-class for errors in this module."""


class InvalidModuleError(Error):
  """The given module is not known to the system."""


class InvalidVersionError(Error):
  """The given module version is not known to the system."""


class InvalidInstancesError(Error):
  """The given instances value is not valid."""


class UnexpectedStateError(Error):
  """An unexpected current state was found when starting/stopping a module."""


class TransientError(Error):
  """A transient error was encountered, retry the operation."""


def get_current_module_name():
  """Returns the module name of the current instance.

  If this is version "v1" of module "module5" for app "my-app", this function
  will return "module5".
  """
  return os.environ.get('GAE_SERVICE') or os.environ.get('CURRENT_MODULE_ID')


def get_current_version_name():
  """Returns the version of the current instance.

  If this is version "v1" of module "module5" for app "my-app", this function
  will return "v1".
  """
  result = os.environ.get('GAE_VERSION')
  if result:
    return result

  result = os.environ['CURRENT_VERSION_ID'].split('.')[0]
  return None if result == 'None' else result


def get_current_instance_id():
  """Returns the ID of the current instance.

  If this is instance 2 of version "v1" of module "module5" for app "my-app",
  this function will return "2".

  This is only valid for automatically-scaled modules; otherwise, None is
  returned.


  Returns:
    String containing the ID of the instance, or None if this is not an
    automatically-scaled module.
  """
  return os.environ.get('GAE_INSTANCE') or os.environ.get('INSTANCE_ID', None)


def _GetRpc():
  return apiproxy_stub_map.UserRPC('modules')


def _MakeAsyncCall(method, request, response, get_result_hook):
  rpc = _GetRpc()
  rpc.make_call(method, request, response, get_result_hook)
  return rpc


_MODULE_SERVICE_ERROR_MAP = {
    modules_service_pb2.ModulesServiceError.INVALID_INSTANCES:
        InvalidInstancesError,
    modules_service_pb2.ModulesServiceError.INVALID_MODULE:
        InvalidModuleError,
    modules_service_pb2.ModulesServiceError.INVALID_VERSION:
        InvalidVersionError,
    modules_service_pb2.ModulesServiceError.TRANSIENT_ERROR:
        TransientError,
    modules_service_pb2.ModulesServiceError.UNEXPECTED_STATE:
        UnexpectedStateError
}


def _CheckAsyncResult(rpc,
                      expected_application_errors,
                      ignored_application_errors):
  try:
    rpc.check_success()
  except apiproxy_errors.ApplicationError as e:
    if e.application_error in ignored_application_errors:
      logging.info(ignored_application_errors.get(e.application_error))
      return
    if e.application_error in expected_application_errors:
      mapped_error = _MODULE_SERVICE_ERROR_MAP.get(e.application_error)
      if mapped_error:
        raise mapped_error()
    raise Error(e)


def get_modules():
  """Returns a list of all modules for the application.

  Returns:
    List of strings containing the names of modules associated with this
      application.  The 'default' module will be included if it exists, as will
      the name of the module that is associated with the instance that calls
      this function.
  """
  def _ResultHook(rpc):
    _CheckAsyncResult(rpc, [], {})


    return rpc.response.module

  request = modules_service_pb2.GetModulesRequest()
  response = modules_service_pb2.GetModulesResponse()
  return _MakeAsyncCall('GetModules',
                        request,
                        response,
                        _ResultHook).get_result()


def get_versions(module=None):
  """Returns a list of versions for a given module.

  Args:
    module: Module to retrieve version for, if None then the current module will
      be used.

  Returns:
    List of strings containing the names of versions associated with the module.
    The current version will also be included in this list.

  Raises:
    InvalidModuleError if the given module isn't valid, TransientError if there
    is an issue fetching the information.
  """
  def _ResultHook(rpc):
    mapped_errors = [modules_service_pb2.ModulesServiceError.INVALID_MODULE,
                     modules_service_pb2.ModulesServiceError.TRANSIENT_ERROR]
    _CheckAsyncResult(rpc, mapped_errors, {})


    return rpc.response.version

  request = modules_service_pb2.GetVersionsRequest()
  if module:
    request.module = module
  response = modules_service_pb2.GetVersionsResponse()
  return _MakeAsyncCall('GetVersions',
                        request,
                        response,
                        _ResultHook).get_result()


def get_default_version(module=None):
  """Returns the name of the default version for the module.

  Args:
    module: Module to retrieve the default version for, if None then the current
      module will be used.

  Returns:
    String containing the name of the default version of the module.

  Raises:
    InvalidModuleError if the given module is not valid, InvalidVersionError if
    no default version could be found.
  """
  def _ResultHook(rpc):
    mapped_errors = [modules_service_pb2.ModulesServiceError.INVALID_MODULE,
                     modules_service_pb2.ModulesServiceError.INVALID_VERSION]
    _CheckAsyncResult(rpc, mapped_errors, {})
    return rpc.response.version

  request = modules_service_pb2.GetDefaultVersionRequest()
  if module:
    request.module = module
  response = modules_service_pb2.GetDefaultVersionResponse()
  return _MakeAsyncCall('GetDefaultVersion',
                        request,
                        response,
                        _ResultHook).get_result()


def get_num_instances(module=None,
                      version=None):
  """Return the number of instances that are set for the given module version.

  This is only valid for fixed modules, an error will be raised for
  automatically-scaled modules.  Support for automatically-scaled modules may be
  supported in the future.

  Args:
    module: String containing the name of the module to fetch this info for, if
      None the module of the current instance will be used.
    version: String containing the name of the version to fetch this info for,
      if None the version of the current instance will be used.  If that version
      does not exist in the other module, then an InvalidVersionError is raised.

  Returns:
    The number of instances that are set for the given module version.

  Raises:
    InvalidVersionError on invalid input.
  """
  def _ResultHook(rpc):
    mapped_errors = [modules_service_pb2.ModulesServiceError.INVALID_VERSION]
    _CheckAsyncResult(rpc, mapped_errors, {})
    return rpc.response.instances

  request = modules_service_pb2.GetNumInstancesRequest()
  if module:
    request.module = module
  if version:
    request.version = version
  response = modules_service_pb2.GetNumInstancesResponse()
  return _MakeAsyncCall('GetNumInstances',
                        request,
                        response,
                        _ResultHook).get_result()


def set_num_instances(instances,
                      module=None, version=None):
  """Sets the number of instances on the module and version.

  Args:
    instances: The number of instances to set.
    module: The module to set the number of instances for, if None the current
      module will be used.
    version: The version set the number of instances for, if None the current
      version will be used.

  Raises:
    InvalidVersionError if the given module version isn't valid, TransientError
    if there is an issue persisting the change.
    TypeError if the given instances type is invalid.
  """
  rpc = set_num_instances_async(instances, module, version)
  rpc.get_result()


def set_num_instances_async(
    instances, module=None, version=None):
  """Returns a UserRPC to set the number of instances on the module version.

  Args:
    instances: The number of instances to set.
    module: The module to set the number of instances for, if None the current
      module will be used.
    version: The version set the number of instances for, if None the current
      version will be used.

  Returns:
    A UserRPC to set the number of instances on the module version.
  """
  def _ResultHook(rpc):
    mapped_errors = [modules_service_pb2.ModulesServiceError.INVALID_VERSION,
                     modules_service_pb2.ModulesServiceError.TRANSIENT_ERROR]
    _CheckAsyncResult(rpc, mapped_errors, {})

  if not isinstance(instances, six.integer_types):
    raise TypeError("'instances' arg must be of type long or int.")
  request = modules_service_pb2.SetNumInstancesRequest()
  request.instances = instances
  if module:
    request.module = module
  if version:
    request.version = version
  response = modules_service_pb2.SetNumInstancesResponse()
  return _MakeAsyncCall('SetNumInstances', request, response, _ResultHook)


def start_version(module, version):
  """Start all instances for the given version of the module.

  Args:
    module: String containing the name of the module to affect.
    version: String containing the name of the version of the module to start.

  Raises:
    InvalidVersionError if the given module version is invalid.
    TransientError if there is a problem persisting the change.
  """
  rpc = start_version_async(module, version)
  rpc.get_result()


def start_version_async(module,
                        version):
  """Returns a UserRPC  to start all instances for the given module version.

  Args:
    module: String containing the name of the module to affect.
    version: String containing the name of the version of the module to start.

  Returns:
    A UserRPC  to start all instances for the given module version.
  """
  def _ResultHook(rpc):
    mapped_errors = [modules_service_pb2.ModulesServiceError.INVALID_VERSION,
                     modules_service_pb2.ModulesServiceError.TRANSIENT_ERROR]
    expected_errors = {
        modules_service_pb2.ModulesServiceError.UNEXPECTED_STATE:
        'The specified module: %s, version: %s is already started.' % (module,
                                                                       version)
    }
    _CheckAsyncResult(rpc, mapped_errors, expected_errors)

  request = modules_service_pb2.StartModuleRequest()
  request.module = module
  request.version = version
  response = modules_service_pb2.StartModuleResponse()
  return _MakeAsyncCall('StartModule', request, response, _ResultHook)


def stop_version(module=None,
                 version=None):
  """Stops all instances for the given version of the module.

  Args:
    module: The module to affect, if None the current module is used.
    version: The version of the given module to affect, if None the current
      version is used.

  Raises:
    InvalidVersionError if the given module version is invalid.
    TransientError if there is a problem persisting the change.
  """
  rpc = stop_version_async(module, version)
  rpc.get_result()


def stop_version_async(module=None,
                       version=None):
  """Returns a UserRPC  to stop all instances for the given module version.

  Args:
    module: The module to affect, if None the current module is used.
    version: The version of the given module to affect, if None the current
      version is used.

  Returns:
    A UserRPC  to stop all instances for the given module version.
  """
  def _ResultHook(rpc):
    mapped_errors = [modules_service_pb2.ModulesServiceError.INVALID_VERSION,
                     modules_service_pb2.ModulesServiceError.TRANSIENT_ERROR]
    expected_errors = {
        modules_service_pb2.ModulesServiceError.UNEXPECTED_STATE:
        'The specified module: %s, version: %s is already stopped.' % (module,
                                                                       version)
    }
    _CheckAsyncResult(rpc, mapped_errors, expected_errors)

  request = modules_service_pb2.StopModuleRequest()
  if module:
    request.module = module
  if version:
    request.version = version
  response = modules_service_pb2.StopModuleResponse()
  return _MakeAsyncCall('StopModule', request, response, _ResultHook)


def get_hostname(module=None,
                 version=None, instance=None):
  """Returns a hostname to use to contact the module.

  Args:
    module: Name of module, if None, take module of the current instance.
    version: Name of version, if version is None then either use the version of
      the current instance if that version exists for the target module,
      otherwise use the default version of the target module.
    instance: Instance to construct a hostname for, if instance is None, a
      loadbalanced hostname for the module will be returned.  If the target
      module is not a fixed module, then instance is not considered valid.

  Returns:
    A valid canonical hostname that can be used to communicate with the given
    module/version/instance.  For example: `0.v1.module5.myapp.appspot.com`

  Raises:
    InvalidModuleError: if the given module version is invalid.
    InvalidInstancesError: if the given instance value is invalid.
    TypeError: if the given instance type is invalid.
  """
  def _ResultHook(rpc):
    mapped_errors = [modules_service_pb2.ModulesServiceError.INVALID_MODULE,
                     modules_service_pb2.ModulesServiceError.INVALID_INSTANCES]
    _CheckAsyncResult(rpc, mapped_errors, [])
    return rpc.response.hostname

  request = modules_service_pb2.GetHostnameRequest()
  if module:
    request.module = module
  if version:
    request.version = version
  if instance or instance == 0:
    if not isinstance(instance, (six.string_types, six.integer_types)):
      raise TypeError(
          "'instance' arg must be of type basestring, long or int.")
    request.instance = str(instance)
  response = modules_service_pb2.GetHostnameResponse()
  return _MakeAsyncCall('GetHostname',
                        request,
                        response,
                        _ResultHook).get_result()
