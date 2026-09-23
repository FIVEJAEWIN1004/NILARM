// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from interfaces_pkg:msg/BasketStatus.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "interfaces_pkg/msg/detail/basket_status__rosidl_typesupport_introspection_c.h"
#include "interfaces_pkg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "interfaces_pkg/msg/detail/basket_status__functions.h"
#include "interfaces_pkg/msg/detail/basket_status__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  interfaces_pkg__msg__BasketStatus__init(message_memory);
}

void interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_fini_function(void * message_memory)
{
  interfaces_pkg__msg__BasketStatus__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_message_member_array[3] = {
  {
    "weight",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(interfaces_pkg__msg__BasketStatus, weight),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "maxweight",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(interfaces_pkg__msg__BasketStatus, maxweight),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "is_full",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(interfaces_pkg__msg__BasketStatus, is_full),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_message_members = {
  "interfaces_pkg__msg",  // message namespace
  "BasketStatus",  // message name
  3,  // number of fields
  sizeof(interfaces_pkg__msg__BasketStatus),
  false,  // has_any_key_member_
  interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_message_member_array,  // message members
  interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_init_function,  // function to initialize message memory (memory has to be allocated)
  interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_message_type_support_handle = {
  0,
  &interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_message_members,
  get_message_typesupport_handle_function,
  &interfaces_pkg__msg__BasketStatus__get_type_hash,
  &interfaces_pkg__msg__BasketStatus__get_type_description,
  &interfaces_pkg__msg__BasketStatus__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_interfaces_pkg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, interfaces_pkg, msg, BasketStatus)() {
  if (!interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_message_type_support_handle.typesupport_identifier) {
    interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &interfaces_pkg__msg__BasketStatus__rosidl_typesupport_introspection_c__BasketStatus_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
