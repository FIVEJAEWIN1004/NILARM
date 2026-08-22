// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from interfaces_pkg:msg/MissionState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/mission_state.hpp"


#ifndef INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__TRAITS_HPP_
#define INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "interfaces_pkg/msg/detail/mission_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace interfaces_pkg
{

namespace msg
{

inline void to_flow_style_yaml(
  const MissionState & msg,
  std::ostream & out)
{
  out << "{";
  // member: state
  {
    out << "state: ";
    rosidl_generator_traits::value_to_yaml(msg.state, out);
    out << ", ";
  }

  // member: harvested_total
  {
    out << "harvested_total: ";
    rosidl_generator_traits::value_to_yaml(msg.harvested_total, out);
    out << ", ";
  }

  // member: goal_count
  {
    out << "goal_count: ";
    rosidl_generator_traits::value_to_yaml(msg.goal_count, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const MissionState & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "state: ";
    rosidl_generator_traits::value_to_yaml(msg.state, out);
    out << "\n";
  }

  // member: harvested_total
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "harvested_total: ";
    rosidl_generator_traits::value_to_yaml(msg.harvested_total, out);
    out << "\n";
  }

  // member: goal_count
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal_count: ";
    rosidl_generator_traits::value_to_yaml(msg.goal_count, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const MissionState & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace interfaces_pkg

namespace rosidl_generator_traits
{

[[deprecated("use interfaces_pkg::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const interfaces_pkg::msg::MissionState & msg,
  std::ostream & out, size_t indentation = 0)
{
  interfaces_pkg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use interfaces_pkg::msg::to_yaml() instead")]]
inline std::string to_yaml(const interfaces_pkg::msg::MissionState & msg)
{
  return interfaces_pkg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<interfaces_pkg::msg::MissionState>()
{
  return "interfaces_pkg::msg::MissionState";
}

template<>
inline const char * name<interfaces_pkg::msg::MissionState>()
{
  return "interfaces_pkg/msg/MissionState";
}

template<>
struct has_fixed_size<interfaces_pkg::msg::MissionState>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<interfaces_pkg::msg::MissionState>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<interfaces_pkg::msg::MissionState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__TRAITS_HPP_
