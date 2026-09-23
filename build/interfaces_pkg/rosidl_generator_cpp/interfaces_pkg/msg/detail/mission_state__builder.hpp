// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_pkg:msg/MissionState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/mission_state.hpp"


#ifndef INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__BUILDER_HPP_
#define INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_pkg/msg/detail/mission_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_pkg
{

namespace msg
{

namespace builder
{

class Init_MissionState_goal_count
{
public:
  explicit Init_MissionState_goal_count(::interfaces_pkg::msg::MissionState & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::msg::MissionState goal_count(::interfaces_pkg::msg::MissionState::_goal_count_type arg)
  {
    msg_.goal_count = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::msg::MissionState msg_;
};

class Init_MissionState_harvested_total
{
public:
  explicit Init_MissionState_harvested_total(::interfaces_pkg::msg::MissionState & msg)
  : msg_(msg)
  {}
  Init_MissionState_goal_count harvested_total(::interfaces_pkg::msg::MissionState::_harvested_total_type arg)
  {
    msg_.harvested_total = std::move(arg);
    return Init_MissionState_goal_count(msg_);
  }

private:
  ::interfaces_pkg::msg::MissionState msg_;
};

class Init_MissionState_state
{
public:
  Init_MissionState_state()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MissionState_harvested_total state(::interfaces_pkg::msg::MissionState::_state_type arg)
  {
    msg_.state = std::move(arg);
    return Init_MissionState_harvested_total(msg_);
  }

private:
  ::interfaces_pkg::msg::MissionState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::msg::MissionState>()
{
  return interfaces_pkg::msg::builder::Init_MissionState_state();
}

}  // namespace interfaces_pkg

#endif  // INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__BUILDER_HPP_
