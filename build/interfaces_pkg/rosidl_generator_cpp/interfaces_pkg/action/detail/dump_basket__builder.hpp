// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_pkg:action/DumpBasket.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/action/dump_basket.hpp"


#ifndef INTERFACES_PKG__ACTION__DETAIL__DUMP_BASKET__BUILDER_HPP_
#define INTERFACES_PKG__ACTION__DETAIL__DUMP_BASKET__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_pkg/action/detail/dump_basket__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_pkg
{

namespace action
{


}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_Goal>()
{
  return ::interfaces_pkg::action::DumpBasket_Goal(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_Result_duration_sec
{
public:
  explicit Init_DumpBasket_Result_duration_sec(::interfaces_pkg::action::DumpBasket_Result & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::action::DumpBasket_Result duration_sec(::interfaces_pkg::action::DumpBasket_Result::_duration_sec_type arg)
  {
    msg_.duration_sec = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_Result msg_;
};

class Init_DumpBasket_Result_success
{
public:
  Init_DumpBasket_Result_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DumpBasket_Result_duration_sec success(::interfaces_pkg::action::DumpBasket_Result::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_DumpBasket_Result_duration_sec(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_Result msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_Result>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_Result_success();
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_Feedback_phase
{
public:
  Init_DumpBasket_Feedback_phase()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::interfaces_pkg::action::DumpBasket_Feedback phase(::interfaces_pkg::action::DumpBasket_Feedback::_phase_type arg)
  {
    msg_.phase = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_Feedback msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_Feedback>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_Feedback_phase();
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_SendGoal_Request_goal
{
public:
  explicit Init_DumpBasket_SendGoal_Request_goal(::interfaces_pkg::action::DumpBasket_SendGoal_Request & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::action::DumpBasket_SendGoal_Request goal(::interfaces_pkg::action::DumpBasket_SendGoal_Request::_goal_type arg)
  {
    msg_.goal = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_SendGoal_Request msg_;
};

class Init_DumpBasket_SendGoal_Request_goal_id
{
public:
  Init_DumpBasket_SendGoal_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DumpBasket_SendGoal_Request_goal goal_id(::interfaces_pkg::action::DumpBasket_SendGoal_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_DumpBasket_SendGoal_Request_goal(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_SendGoal_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_SendGoal_Request>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_SendGoal_Request_goal_id();
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_SendGoal_Response_stamp
{
public:
  explicit Init_DumpBasket_SendGoal_Response_stamp(::interfaces_pkg::action::DumpBasket_SendGoal_Response & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::action::DumpBasket_SendGoal_Response stamp(::interfaces_pkg::action::DumpBasket_SendGoal_Response::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_SendGoal_Response msg_;
};

class Init_DumpBasket_SendGoal_Response_accepted
{
public:
  Init_DumpBasket_SendGoal_Response_accepted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DumpBasket_SendGoal_Response_stamp accepted(::interfaces_pkg::action::DumpBasket_SendGoal_Response::_accepted_type arg)
  {
    msg_.accepted = std::move(arg);
    return Init_DumpBasket_SendGoal_Response_stamp(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_SendGoal_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_SendGoal_Response>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_SendGoal_Response_accepted();
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_SendGoal_Event_response
{
public:
  explicit Init_DumpBasket_SendGoal_Event_response(::interfaces_pkg::action::DumpBasket_SendGoal_Event & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::action::DumpBasket_SendGoal_Event response(::interfaces_pkg::action::DumpBasket_SendGoal_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_SendGoal_Event msg_;
};

class Init_DumpBasket_SendGoal_Event_request
{
public:
  explicit Init_DumpBasket_SendGoal_Event_request(::interfaces_pkg::action::DumpBasket_SendGoal_Event & msg)
  : msg_(msg)
  {}
  Init_DumpBasket_SendGoal_Event_response request(::interfaces_pkg::action::DumpBasket_SendGoal_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_DumpBasket_SendGoal_Event_response(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_SendGoal_Event msg_;
};

class Init_DumpBasket_SendGoal_Event_info
{
public:
  Init_DumpBasket_SendGoal_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DumpBasket_SendGoal_Event_request info(::interfaces_pkg::action::DumpBasket_SendGoal_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_DumpBasket_SendGoal_Event_request(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_SendGoal_Event msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_SendGoal_Event>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_SendGoal_Event_info();
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_GetResult_Request_goal_id
{
public:
  Init_DumpBasket_GetResult_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::interfaces_pkg::action::DumpBasket_GetResult_Request goal_id(::interfaces_pkg::action::DumpBasket_GetResult_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_GetResult_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_GetResult_Request>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_GetResult_Request_goal_id();
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_GetResult_Response_result
{
public:
  explicit Init_DumpBasket_GetResult_Response_result(::interfaces_pkg::action::DumpBasket_GetResult_Response & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::action::DumpBasket_GetResult_Response result(::interfaces_pkg::action::DumpBasket_GetResult_Response::_result_type arg)
  {
    msg_.result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_GetResult_Response msg_;
};

class Init_DumpBasket_GetResult_Response_status
{
public:
  Init_DumpBasket_GetResult_Response_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DumpBasket_GetResult_Response_result status(::interfaces_pkg::action::DumpBasket_GetResult_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_DumpBasket_GetResult_Response_result(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_GetResult_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_GetResult_Response>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_GetResult_Response_status();
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_GetResult_Event_response
{
public:
  explicit Init_DumpBasket_GetResult_Event_response(::interfaces_pkg::action::DumpBasket_GetResult_Event & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::action::DumpBasket_GetResult_Event response(::interfaces_pkg::action::DumpBasket_GetResult_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_GetResult_Event msg_;
};

class Init_DumpBasket_GetResult_Event_request
{
public:
  explicit Init_DumpBasket_GetResult_Event_request(::interfaces_pkg::action::DumpBasket_GetResult_Event & msg)
  : msg_(msg)
  {}
  Init_DumpBasket_GetResult_Event_response request(::interfaces_pkg::action::DumpBasket_GetResult_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_DumpBasket_GetResult_Event_response(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_GetResult_Event msg_;
};

class Init_DumpBasket_GetResult_Event_info
{
public:
  Init_DumpBasket_GetResult_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DumpBasket_GetResult_Event_request info(::interfaces_pkg::action::DumpBasket_GetResult_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_DumpBasket_GetResult_Event_request(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_GetResult_Event msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_GetResult_Event>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_GetResult_Event_info();
}

}  // namespace interfaces_pkg


namespace interfaces_pkg
{

namespace action
{

namespace builder
{

class Init_DumpBasket_FeedbackMessage_feedback
{
public:
  explicit Init_DumpBasket_FeedbackMessage_feedback(::interfaces_pkg::action::DumpBasket_FeedbackMessage & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::action::DumpBasket_FeedbackMessage feedback(::interfaces_pkg::action::DumpBasket_FeedbackMessage::_feedback_type arg)
  {
    msg_.feedback = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_FeedbackMessage msg_;
};

class Init_DumpBasket_FeedbackMessage_goal_id
{
public:
  Init_DumpBasket_FeedbackMessage_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DumpBasket_FeedbackMessage_feedback goal_id(::interfaces_pkg::action::DumpBasket_FeedbackMessage::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_DumpBasket_FeedbackMessage_feedback(msg_);
  }

private:
  ::interfaces_pkg::action::DumpBasket_FeedbackMessage msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::action::DumpBasket_FeedbackMessage>()
{
  return interfaces_pkg::action::builder::Init_DumpBasket_FeedbackMessage_goal_id();
}

}  // namespace interfaces_pkg

#endif  // INTERFACES_PKG__ACTION__DETAIL__DUMP_BASKET__BUILDER_HPP_
