/*
Copyright 2023 The Kubernetes Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

// Package cm (abbreviation of "container manager") and its subpackages contain all the kubelet code
// to manage containers. The container manager is a core kubelet subsystem responsible for
// configuring containers' cgroups, enforcing Quality of Service (QoS) policies, and allocating
// compute resources such as CPUs, memory, and devices.
//
// # ContainerManager Interface
//
// The central abstraction is the ContainerManager interface, defined in container_manager.go.
// It provides methods for the kubelet to:
//
//   - Set up and manage the node's cgroup hierarchy for pods and containers
//   - Enforce resource limits and requests based on the pod's QoS class
//   - Allocate and reclaim compute resources (CPU, memory, devices)
//   - Report resource capacity and allocatable amounts to the API server
//   - Manage pod-level cgroups when the --cgroups-per-qos flag is enabled
//
// The ContainerManager is initialized during kubelet startup and coordinates with other
// kubelet components such as the pod lifecycle manager and the status manager.
//
// # Cgroup Management
//
// The container manager is responsible for creating and maintaining the cgroup hierarchy
// used by the kubelet. When cgroups-per-qos is enabled, the manager creates a two-level
// hierarchy:
//
//   - QoS-level cgroups: /kubepods/burstable and /kubepods/besteffort segregate pods
//     by their QoS class (Guaranteed, Burstable, BestEffort)
//   - Pod-level cgroups: each pod receives its own cgroup under its QoS parent
//
// The package supports both cgroup v1 and cgroup v2. Under cgroup v2, the unified
// hierarchy simplifies resource accounting and enables features such as memory.swap
// controls and PSI (Pressure Stall Information) monitoring. The CgroupManager
// abstraction handles differences between the two versions transparently.
//
// # QoS Enforcement
//
// The container manager enforces Kubernetes QoS classes by configuring appropriate
// cgroup limits:
//
//   - Guaranteed pods: resource requests equal limits; cgroups are set with strict
//     CPU and memory limits
//   - Burstable pods: resource requests are less than limits; cgroups enforce
//     requests as reservations and limits as hard caps
//   - BestEffort pods: no resource requests or limits; these pods share remaining
//     resources and are the first to be evicted under pressure
//
// The QoS cgroup manager also sets system-reserved and kube-reserved resources to
// protect node stability and kubelet operation.
//
// # Resource Allocation
//
// Resource allocation is delegated to specialized sub-managers, each handling a
// specific resource type. The container manager coordinates these sub-managers
// during pod admission and container creation:
//
//   - CPU allocation: handled by the cpumanager subpackage
//   - Memory allocation: handled by the memorymanager subpackage
//   - Topology-aware allocation: handled by the topologymanager subpackage
//   - Device allocation: handled by the devicemanager subpackage
//
// # Subpackages
//
//   - cpumanager: Implements CPU affinity policies for containers. Supports a
//     "static" policy that assigns exclusive CPUs to Guaranteed pods with integer
//     CPU requests, and a "none" policy that uses the default CFS scheduler.
//
//   - memorymanager: Implements NUMA-aware memory allocation policies. The "static"
//     policy pins container memory to specific NUMA nodes to reduce cross-node
//     memory access latency.
//
//   - topologymanager: Coordinates resource alignment across CPU, memory, and device
//     managers to ensure resources are allocated from the same NUMA node when possible.
//     Supports multiple policies: "none", "best-effort", "restricted", and
//     "single-numa-node".
//
//   - devicemanager: Implements the Kubernetes Device Plugin framework. It manages
//     the lifecycle of device plugins, handles device allocation requests from
//     containers, and reports device capacity to the kubelet. Devices are advertised
//     as extended resources (e.g., nvidia.com/gpu).
//
// # Platform Differences
//
// The container manager has platform-specific implementations:
//
//   - Linux (container_manager_linux.go): Full implementation including cgroup
//     management (v1 and v2), CPU/memory/device/topology managers, and support for
//     all QoS enforcement features. This is the primary and most complete
//     implementation.
//
//   - Windows (container_manager_windows.go): Provides a subset of functionality
//     adapted to Windows container isolation. Windows uses job objects rather than
//     cgroups for resource isolation. Some features such as CPU pinning and NUMA
//     awareness are not available on Windows.
//
//   - Unsupported platforms: A stub implementation (container_manager_stub.go) is
//     provided for platforms where container management is not supported.
package cm
