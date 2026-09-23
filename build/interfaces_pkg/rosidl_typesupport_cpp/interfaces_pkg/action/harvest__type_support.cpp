// generated from rosidl_typesupport_cpp/resource/idl__type_support.cpp.em
// with input from interfaces_pkg:action/Harvest.idl
// generated code does not contain a copyright notice

#include "cstddef"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "interfaces_pkg/action/detail/harvest__functions.h"
#include "interfaces_pkg/action/detail/harvest__struct.hpp"
#include "rosidl_typesupport_cpp/identifier.hpp"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
#include "rosidl_typesupport_cpp/visibility_control.h"
#include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_Goal_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_Goal_type_support_ids_t;

static const _Harvest_Goal_type_support_ids_t _Harvest_Goal_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_Goal_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_Goal_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_Goal_type_support_symbol_names_t _Harvest_Goal_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_Goal)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_Goal)),
  }
};

typedef struct _Harvest_Goal_type_support_data_t
{
  void * data[2];
} _Harvest_Goal_type_support_data_t;

static _Harvest_Goal_type_support_data_t _Harvest_Goal_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_Goal_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_Goal_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_Goal_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_Goal_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_Goal_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_Goal_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_Goal__get_type_hash,
  &interfaces_pkg__action__Harvest_Goal__get_type_description,
  &interfaces_pkg__action__Harvest_Goal__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_Goal>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_Goal_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_Goal)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_Goal>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_Result_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_Result_type_support_ids_t;

static const _Harvest_Result_type_support_ids_t _Harvest_Result_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_Result_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_Result_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_Result_type_support_symbol_names_t _Harvest_Result_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_Result)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_Result)),
  }
};

typedef struct _Harvest_Result_type_support_data_t
{
  void * data[2];
} _Harvest_Result_type_support_data_t;

static _Harvest_Result_type_support_data_t _Harvest_Result_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_Result_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_Result_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_Result_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_Result_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_Result_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_Result_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_Result__get_type_hash,
  &interfaces_pkg__action__Harvest_Result__get_type_description,
  &interfaces_pkg__action__Harvest_Result__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_Result>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_Result_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_Result)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_Result>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_Feedback_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_Feedback_type_support_ids_t;

static const _Harvest_Feedback_type_support_ids_t _Harvest_Feedback_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_Feedback_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_Feedback_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_Feedback_type_support_symbol_names_t _Harvest_Feedback_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_Feedback)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_Feedback)),
  }
};

typedef struct _Harvest_Feedback_type_support_data_t
{
  void * data[2];
} _Harvest_Feedback_type_support_data_t;

static _Harvest_Feedback_type_support_data_t _Harvest_Feedback_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_Feedback_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_Feedback_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_Feedback_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_Feedback_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_Feedback_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_Feedback_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_Feedback__get_type_hash,
  &interfaces_pkg__action__Harvest_Feedback__get_type_description,
  &interfaces_pkg__action__Harvest_Feedback__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_Feedback>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_Feedback_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_Feedback)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_Feedback>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_SendGoal_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_SendGoal_Request_type_support_ids_t;

static const _Harvest_SendGoal_Request_type_support_ids_t _Harvest_SendGoal_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_SendGoal_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_SendGoal_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_SendGoal_Request_type_support_symbol_names_t _Harvest_SendGoal_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_SendGoal_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_SendGoal_Request)),
  }
};

typedef struct _Harvest_SendGoal_Request_type_support_data_t
{
  void * data[2];
} _Harvest_SendGoal_Request_type_support_data_t;

static _Harvest_SendGoal_Request_type_support_data_t _Harvest_SendGoal_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_SendGoal_Request_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_SendGoal_Request_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_SendGoal_Request_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_SendGoal_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_SendGoal_Request_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_SendGoal_Request_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_SendGoal_Request__get_type_hash,
  &interfaces_pkg__action__Harvest_SendGoal_Request__get_type_description,
  &interfaces_pkg__action__Harvest_SendGoal_Request__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Request>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_SendGoal_Request_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_SendGoal_Request)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Request>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_SendGoal_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_SendGoal_Response_type_support_ids_t;

static const _Harvest_SendGoal_Response_type_support_ids_t _Harvest_SendGoal_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_SendGoal_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_SendGoal_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_SendGoal_Response_type_support_symbol_names_t _Harvest_SendGoal_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_SendGoal_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_SendGoal_Response)),
  }
};

typedef struct _Harvest_SendGoal_Response_type_support_data_t
{
  void * data[2];
} _Harvest_SendGoal_Response_type_support_data_t;

static _Harvest_SendGoal_Response_type_support_data_t _Harvest_SendGoal_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_SendGoal_Response_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_SendGoal_Response_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_SendGoal_Response_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_SendGoal_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_SendGoal_Response_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_SendGoal_Response_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_SendGoal_Response__get_type_hash,
  &interfaces_pkg__action__Harvest_SendGoal_Response__get_type_description,
  &interfaces_pkg__action__Harvest_SendGoal_Response__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Response>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_SendGoal_Response_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_SendGoal_Response)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Response>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_SendGoal_Event_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_SendGoal_Event_type_support_ids_t;

static const _Harvest_SendGoal_Event_type_support_ids_t _Harvest_SendGoal_Event_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_SendGoal_Event_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_SendGoal_Event_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_SendGoal_Event_type_support_symbol_names_t _Harvest_SendGoal_Event_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_SendGoal_Event)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_SendGoal_Event)),
  }
};

typedef struct _Harvest_SendGoal_Event_type_support_data_t
{
  void * data[2];
} _Harvest_SendGoal_Event_type_support_data_t;

static _Harvest_SendGoal_Event_type_support_data_t _Harvest_SendGoal_Event_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_SendGoal_Event_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_SendGoal_Event_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_SendGoal_Event_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_SendGoal_Event_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_SendGoal_Event_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_SendGoal_Event_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_SendGoal_Event__get_type_hash,
  &interfaces_pkg__action__Harvest_SendGoal_Event__get_type_description,
  &interfaces_pkg__action__Harvest_SendGoal_Event__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Event>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_SendGoal_Event_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_SendGoal_Event)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Event>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
#include "rosidl_runtime_c/service_type_support_struct.h"
#include "rosidl_typesupport_cpp/service_type_support.hpp"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_cpp/service_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_SendGoal_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_SendGoal_type_support_ids_t;

static const _Harvest_SendGoal_type_support_ids_t _Harvest_SendGoal_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_SendGoal_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_SendGoal_type_support_symbol_names_t;
#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_SendGoal_type_support_symbol_names_t _Harvest_SendGoal_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_SendGoal)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_SendGoal)),
  }
};

typedef struct _Harvest_SendGoal_type_support_data_t
{
  void * data[2];
} _Harvest_SendGoal_type_support_data_t;

static _Harvest_SendGoal_type_support_data_t _Harvest_SendGoal_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_SendGoal_service_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_SendGoal_service_typesupport_ids.typesupport_identifier[0],
  &_Harvest_SendGoal_service_typesupport_symbol_names.symbol_name[0],
  &_Harvest_SendGoal_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t Harvest_SendGoal_service_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_SendGoal_service_typesupport_map),
  ::rosidl_typesupport_cpp::get_service_typesupport_handle_function,
  ::rosidl_typesupport_cpp::get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Request>(),
  ::rosidl_typesupport_cpp::get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Response>(),
  ::rosidl_typesupport_cpp::get_message_type_support_handle<interfaces_pkg::action::Harvest_SendGoal_Event>(),
  &::rosidl_typesupport_cpp::service_create_event_message<interfaces_pkg::action::Harvest_SendGoal>,
  &::rosidl_typesupport_cpp::service_destroy_event_message<interfaces_pkg::action::Harvest_SendGoal>,
  &interfaces_pkg__action__Harvest_SendGoal__get_type_hash,
  &interfaces_pkg__action__Harvest_SendGoal__get_type_description,
  &interfaces_pkg__action__Harvest_SendGoal__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
get_service_type_support_handle<interfaces_pkg::action::Harvest_SendGoal>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_SendGoal_service_type_support_handle;
}

}  // namespace rosidl_typesupport_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_SendGoal)() {
  return ::rosidl_typesupport_cpp::get_service_type_support_handle<interfaces_pkg::action::Harvest_SendGoal>();
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_GetResult_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_GetResult_Request_type_support_ids_t;

static const _Harvest_GetResult_Request_type_support_ids_t _Harvest_GetResult_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_GetResult_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_GetResult_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_GetResult_Request_type_support_symbol_names_t _Harvest_GetResult_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_GetResult_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_GetResult_Request)),
  }
};

typedef struct _Harvest_GetResult_Request_type_support_data_t
{
  void * data[2];
} _Harvest_GetResult_Request_type_support_data_t;

static _Harvest_GetResult_Request_type_support_data_t _Harvest_GetResult_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_GetResult_Request_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_GetResult_Request_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_GetResult_Request_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_GetResult_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_GetResult_Request_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_GetResult_Request_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_GetResult_Request__get_type_hash,
  &interfaces_pkg__action__Harvest_GetResult_Request__get_type_description,
  &interfaces_pkg__action__Harvest_GetResult_Request__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Request>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_GetResult_Request_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_GetResult_Request)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Request>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_GetResult_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_GetResult_Response_type_support_ids_t;

static const _Harvest_GetResult_Response_type_support_ids_t _Harvest_GetResult_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_GetResult_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_GetResult_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_GetResult_Response_type_support_symbol_names_t _Harvest_GetResult_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_GetResult_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_GetResult_Response)),
  }
};

typedef struct _Harvest_GetResult_Response_type_support_data_t
{
  void * data[2];
} _Harvest_GetResult_Response_type_support_data_t;

static _Harvest_GetResult_Response_type_support_data_t _Harvest_GetResult_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_GetResult_Response_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_GetResult_Response_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_GetResult_Response_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_GetResult_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_GetResult_Response_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_GetResult_Response_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_GetResult_Response__get_type_hash,
  &interfaces_pkg__action__Harvest_GetResult_Response__get_type_description,
  &interfaces_pkg__action__Harvest_GetResult_Response__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Response>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_GetResult_Response_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_GetResult_Response)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Response>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_GetResult_Event_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_GetResult_Event_type_support_ids_t;

static const _Harvest_GetResult_Event_type_support_ids_t _Harvest_GetResult_Event_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_GetResult_Event_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_GetResult_Event_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_GetResult_Event_type_support_symbol_names_t _Harvest_GetResult_Event_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_GetResult_Event)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_GetResult_Event)),
  }
};

typedef struct _Harvest_GetResult_Event_type_support_data_t
{
  void * data[2];
} _Harvest_GetResult_Event_type_support_data_t;

static _Harvest_GetResult_Event_type_support_data_t _Harvest_GetResult_Event_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_GetResult_Event_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_GetResult_Event_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_GetResult_Event_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_GetResult_Event_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_GetResult_Event_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_GetResult_Event_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_GetResult_Event__get_type_hash,
  &interfaces_pkg__action__Harvest_GetResult_Event__get_type_description,
  &interfaces_pkg__action__Harvest_GetResult_Event__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Event>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_GetResult_Event_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_GetResult_Event)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Event>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "rosidl_typesupport_cpp/service_type_support.hpp"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/service_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_GetResult_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_GetResult_type_support_ids_t;

static const _Harvest_GetResult_type_support_ids_t _Harvest_GetResult_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_GetResult_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_GetResult_type_support_symbol_names_t;
#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_GetResult_type_support_symbol_names_t _Harvest_GetResult_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_GetResult)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_GetResult)),
  }
};

typedef struct _Harvest_GetResult_type_support_data_t
{
  void * data[2];
} _Harvest_GetResult_type_support_data_t;

static _Harvest_GetResult_type_support_data_t _Harvest_GetResult_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_GetResult_service_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_GetResult_service_typesupport_ids.typesupport_identifier[0],
  &_Harvest_GetResult_service_typesupport_symbol_names.symbol_name[0],
  &_Harvest_GetResult_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t Harvest_GetResult_service_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_GetResult_service_typesupport_map),
  ::rosidl_typesupport_cpp::get_service_typesupport_handle_function,
  ::rosidl_typesupport_cpp::get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Request>(),
  ::rosidl_typesupport_cpp::get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Response>(),
  ::rosidl_typesupport_cpp::get_message_type_support_handle<interfaces_pkg::action::Harvest_GetResult_Event>(),
  &::rosidl_typesupport_cpp::service_create_event_message<interfaces_pkg::action::Harvest_GetResult>,
  &::rosidl_typesupport_cpp::service_destroy_event_message<interfaces_pkg::action::Harvest_GetResult>,
  &interfaces_pkg__action__Harvest_GetResult__get_type_hash,
  &interfaces_pkg__action__Harvest_GetResult__get_type_description,
  &interfaces_pkg__action__Harvest_GetResult__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
get_service_type_support_handle<interfaces_pkg::action::Harvest_GetResult>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_GetResult_service_type_support_handle;
}

}  // namespace rosidl_typesupport_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_GetResult)() {
  return ::rosidl_typesupport_cpp::get_service_type_support_handle<interfaces_pkg::action::Harvest_GetResult>();
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__functions.h"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

typedef struct _Harvest_FeedbackMessage_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Harvest_FeedbackMessage_type_support_ids_t;

static const _Harvest_FeedbackMessage_type_support_ids_t _Harvest_FeedbackMessage_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _Harvest_FeedbackMessage_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Harvest_FeedbackMessage_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Harvest_FeedbackMessage_type_support_symbol_names_t _Harvest_FeedbackMessage_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, interfaces_pkg, action, Harvest_FeedbackMessage)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_pkg, action, Harvest_FeedbackMessage)),
  }
};

typedef struct _Harvest_FeedbackMessage_type_support_data_t
{
  void * data[2];
} _Harvest_FeedbackMessage_type_support_data_t;

static _Harvest_FeedbackMessage_type_support_data_t _Harvest_FeedbackMessage_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Harvest_FeedbackMessage_message_typesupport_map = {
  2,
  "interfaces_pkg",
  &_Harvest_FeedbackMessage_message_typesupport_ids.typesupport_identifier[0],
  &_Harvest_FeedbackMessage_message_typesupport_symbol_names.symbol_name[0],
  &_Harvest_FeedbackMessage_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Harvest_FeedbackMessage_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Harvest_FeedbackMessage_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
  &interfaces_pkg__action__Harvest_FeedbackMessage__get_type_hash,
  &interfaces_pkg__action__Harvest_FeedbackMessage__get_type_description,
  &interfaces_pkg__action__Harvest_FeedbackMessage__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_pkg::action::Harvest_FeedbackMessage>()
{
  return &::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_FeedbackMessage_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest_FeedbackMessage)() {
  return get_message_type_support_handle<interfaces_pkg::action::Harvest_FeedbackMessage>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

#include "action_msgs/msg/goal_status_array.hpp"
#include "action_msgs/srv/cancel_goal.hpp"
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
#include "rosidl_runtime_c/action_type_support_struct.h"
#include "rosidl_typesupport_cpp/action_type_support.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_cpp/service_type_support.hpp"

namespace interfaces_pkg
{

namespace action
{

namespace rosidl_typesupport_cpp
{

static rosidl_action_type_support_t Harvest_action_type_support_handle = {
  NULL, NULL, NULL, NULL, NULL,
  &interfaces_pkg__action__Harvest__get_type_hash,
  &interfaces_pkg__action__Harvest__get_type_description,
  &interfaces_pkg__action__Harvest__get_type_description_sources,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace action

}  // namespace interfaces_pkg

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_action_type_support_t *
get_action_type_support_handle<interfaces_pkg::action::Harvest>()
{
  using ::interfaces_pkg::action::rosidl_typesupport_cpp::Harvest_action_type_support_handle;
  // Thread-safe by always writing the same values to the static struct
  Harvest_action_type_support_handle.goal_service_type_support = get_service_type_support_handle<::interfaces_pkg::action::Harvest::Impl::SendGoalService>();
  Harvest_action_type_support_handle.result_service_type_support = get_service_type_support_handle<::interfaces_pkg::action::Harvest::Impl::GetResultService>();
  Harvest_action_type_support_handle.cancel_service_type_support = get_service_type_support_handle<::interfaces_pkg::action::Harvest::Impl::CancelGoalService>();
  Harvest_action_type_support_handle.feedback_message_type_support = get_message_type_support_handle<::interfaces_pkg::action::Harvest::Impl::FeedbackMessage>();
  Harvest_action_type_support_handle.status_message_type_support = get_message_type_support_handle<::interfaces_pkg::action::Harvest::Impl::GoalStatusMessage>();
  return &Harvest_action_type_support_handle;
}

}  // namespace rosidl_typesupport_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_action_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__ACTION_SYMBOL_NAME(rosidl_typesupport_cpp, interfaces_pkg, action, Harvest)() {
  return ::rosidl_typesupport_cpp::get_action_type_support_handle<interfaces_pkg::action::Harvest>();
}

#ifdef __cplusplus
}
#endif
