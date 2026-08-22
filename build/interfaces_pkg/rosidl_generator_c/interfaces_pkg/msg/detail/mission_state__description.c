// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from interfaces_pkg:msg/MissionState.idl
// generated code does not contain a copyright notice

#include "interfaces_pkg/msg/detail/mission_state__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_interfaces_pkg
const rosidl_type_hash_t *
interfaces_pkg__msg__MissionState__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xf2, 0x8f, 0x25, 0x55, 0x3d, 0xef, 0xa3, 0x79,
      0xfe, 0xcc, 0xc5, 0x2e, 0xe3, 0x32, 0x10, 0xa4,
      0xbc, 0x2d, 0xde, 0xdf, 0x46, 0xd3, 0x72, 0x22,
      0x74, 0x8a, 0xd1, 0x57, 0x79, 0x9a, 0x49, 0xbe,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char interfaces_pkg__msg__MissionState__TYPE_NAME[] = "interfaces_pkg/msg/MissionState";

// Define type names, field names, and default values
static char interfaces_pkg__msg__MissionState__FIELD_NAME__state[] = "state";
static char interfaces_pkg__msg__MissionState__FIELD_NAME__harvested_total[] = "harvested_total";
static char interfaces_pkg__msg__MissionState__FIELD_NAME__goal_count[] = "goal_count";

static rosidl_runtime_c__type_description__Field interfaces_pkg__msg__MissionState__FIELDS[] = {
  {
    {interfaces_pkg__msg__MissionState__FIELD_NAME__state, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {interfaces_pkg__msg__MissionState__FIELD_NAME__harvested_total, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {interfaces_pkg__msg__MissionState__FIELD_NAME__goal_count, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
interfaces_pkg__msg__MissionState__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {interfaces_pkg__msg__MissionState__TYPE_NAME, 31, 31},
      {interfaces_pkg__msg__MissionState__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "string state               # \"IDLE\",\"NAV_TO_LOADING\",\"HARVEST\",\"DUMP\",\"CHECK_GOAL\",\"NAV_TO_UNLOAD\",\"COMPLETE\",\"ERROR\"\n"
  "int32 harvested_total      # \\xec\\xa7\\x80\\xea\\xb8\\x88\\xea\\xb9\\x8c\\xec\\xa7\\x80 \\xeb\\x88\\x84\\xec\\xa0\\x81 \\xec\\x88\\x98\\xed\\x99\\x95 \\xea\\xb0\\x9c\\xec\\x88\\x98\n"
  "int32 goal_count            # \\xeb\\xaa\\xa9\\xed\\x91\\x9c \\xec\\x88\\x98\\xed\\x99\\x95 \\xea\\xb0\\x9c\\xec\\x88\\x98";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
interfaces_pkg__msg__MissionState__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {interfaces_pkg__msg__MissionState__TYPE_NAME, 31, 31},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 200, 200},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
interfaces_pkg__msg__MissionState__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *interfaces_pkg__msg__MissionState__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
