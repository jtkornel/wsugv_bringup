# Copyright (c) 2024, Stogl Robotics Consulting UG (haftungsbeschränkt)
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
# Source of this file are templates in
# [RosTeamWorkspace](https://github.com/StoglRobotics/ros_team_workspace) repository.
#
# Author: Dr. Denis
#

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, TimerAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Declare arguments
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "description_package",
            default_value="wsugv_description",
            description="Description package with robot URDF/xacro files. Usually the argument \
        is not set, it enables use of a custom description.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_file",
            default_value="wsugv.urdf.xacro",
            description="URDF/XACRO description file with the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "prefix",
            default_value='""',
            description="Prefix of the joint names, useful for \
        multi-robot setup. If changed than also joint names in the controllers' configuration \
        have to be updated.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "rviz",
            default_value="true",
            description="Launch the RVIZ gui",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "teleop",
            default_value="true",
            description="Launch joystick teleop"
            )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_mock_hardware",
            default_value="true",
            description="Start robot with mock hardware mirroring command to its states.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "mock_sensor_commands",
            default_value="false",
            description="Enable mock command interfaces for sensors used for simple simulations. \
            Used only if 'use_mock_hardware' parameter is true.",
        )
    )

    # Initialize Arguments
    description_package = LaunchConfiguration("description_package")
    description_file = LaunchConfiguration("description_file")
    prefix = LaunchConfiguration("prefix")
    use_mock_hardware = LaunchConfiguration("use_mock_hardware")
    mock_sensor_commands = LaunchConfiguration("mock_sensor_commands")
    launch_rviz = LaunchConfiguration("rviz")
    launch_teleop = LaunchConfiguration("teleop")

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare(description_package), "urdf", description_file]
            ),
            " ",
            "prefix:=",
            prefix,
            " ",
            "use_mock_hardware:=",
            use_mock_hardware,
            " ",
            "mock_sensor_commands:=",
            mock_sensor_commands,
            " ",
        ]
    )

    robot_description = {"robot_description": robot_description_content}

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare(description_package), "rviz", "wsugv.rviz"]
    )

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )
    ws_ugv_node = Node(
        package="ws_ugv_protocol",
        executable="ws_ugv_protocol",
        name="ws_ugv_communication_protocol",
        output="both"
    )
    
    lidar_launch_file = PathJoinSubstitution([FindPackageShare("sllidar_ros2"), "launch", "sllidar_a1_launch.py"])
    lidar_launch = IncludeLaunchDescription(lidar_launch_file)

    teleop_launch_file = PathJoinSubstitution([FindPackageShare("teleop_twist_joy"), "launch", "teleop-launch.py"])
    teleop_config_file = PathJoinSubstitution([FindPackageShare("wsugv_bringup"), "launch", "teleop_joy.yaml"])
    teleop_launch = IncludeLaunchDescription(teleop_launch_file,
                                             condition=IfCondition(launch_teleop),
                                             launch_arguments={ "config_filepath": teleop_config_file }.items())


    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        condition=IfCondition(launch_rviz),
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
    )

    launch_actions =  [
            robot_state_pub_node,
            ws_ugv_node,
            lidar_launch,
            teleop_launch,
            rviz_node
        ]    

    return LaunchDescription(
        declared_arguments
        + launch_actions
    )
