# Rollback Scenarios

## Application Outage Scenarios

- id: application_outage
- module: krkn/scenario_plugins/application_outage/application_outage_scenario_plugin.py

### What


Create `NetworkPolicy` to block all traffic to the application pods, then sleep `duration` seconds, and finally delete the `NetworkPolicy`.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
    name: krkn-deny-<get_random_string(5)>
spec:
    podSelector:
    matchLabels: {{ pod_selector }}
    policyTypes: {{ traffic_type }}
```

### Rollback

- need: yes
- resource: `NetworkPolicy`

Set deleting corresponding `NetworkPolicy` callable to version file.

## Container Scenarios

- id: container
- module: krkn/scenario_plugins/container/container_scenario_plugin.py

### What

Kill specific containers (can be multiple) in the pod, then sleep `duration` seconds, and will retry on killing the containers if they are still running.

### Rollback

- need: no
- resource: None

No rollback needed, as the containers will be restarted by Kubernetes automatically.

## Hog Scenarios

- id: hogs
- module: krkn/scenario_plugins/hogs/hogs_scenario_plugin.py

### What

Use `lib_k8s.deploy_hog` to deploy hog pods, and then sleep `duration` seconds.
While sleeping, will also collects the CPU, Memory, Disk space sample for the nodes.

### Rollback

- need: yes
- resource: `Pod`

Set deleting hog pods callable to version file.

## Managed Cluster Scenarios

- id: managed_cluster
- module: krkn/scenario_plugins/managed_cluster/managed_cluster_scenario_plugin.py

### What

Provides scenarios to test Open Cluster Management (OCM) or Red Hat Advanced Cluster Management by injecting faults with `ManifestWork` into ManagedClusters. The following actions are supported:
- Start/stop/restart ManagedCluster instances by scaling deployments
- Start/stop/restart the klusterlet agents
- All scenarios use ManifestWork resources to execute commands on the managed clusters

### Rollback

- need: unknown
- resource: `ManifestWork`

Not sure do we need to rollback for this plugin, as it depends on the command executed in `ManifestWork`.


## Native Scenario Plugin

- id: native
- module: krkn/scenario_plugins/native/native_scenario_plugin.py

### What

Leverage [arcaflow_plugin_sdk](https://github.com/arcalot/arcaflow-plugin-sdk-python/tree/main?tab=readme-ov-file) to execute the following steps:

```python
PLUGINS = Plugins(
    [
        PluginStep(
            kill_pods,
            [
                "error",
            ],
        ),
        PluginStep(wait_for_pods, ["error"]),
        PluginStep(run_python_file, ["error"]),
        PluginStep(network_chaos, ["error"]), # will create network chaos job
        PluginStep(pod_outage, ["error"]), # will create pod outage job
        PluginStep(pod_egress_shaping, ["error"]), # will create pod egress shaping job
        PluginStep(pod_ingress_shaping, ["error"]), # will create pod ingress shaping job
    ]
)
```

### Rollback

- need: yes
- resource: `Job`

Set `delete_job` callable to version file in each `PluginStep` to clean up the chaos jobs properly after the scenario duration.


## Network Chaos Scenarios

- id: network_chaos
- module: krkn/scenario_plugins/network_chaos/network_chaos_scenario_plugin.py

### What

Creates network disruption on specified nodes by deploying `job` that apply network chaos conditions like bandwidth limitations, latency, or packet loss to specific network interfaces. Can run in serial or parallel mode across multiple nodes.

`krkn/scenario_plugins/network_chaos/job.j2`  
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: chaos-{{jobname}}
spec:
  template:
    spec:
      nodeName: {{nodename}}
      hostNetwork: true
      containers:
      - name: networkchaos
        image: docker.io/fedora/tools
        command: ["/bin/sh",  "-c", "{{cmd}}"]
        securityContext:
          privileged: true
        volumeMounts:
          - mountPath: /lib/modules
            name: lib-modules
            readOnly: true
      volumes:
        - name: lib-modules
          hostPath:
            path: /lib/modules
      restartPolicy: Never
  backoffLimit: 0
```

### Rollback

- need: yes
- resource: `Job`

Set `delete_job` callable to version file to clean up the chaos job properly after the scenario duration.

## Network Chaos NG Scenarios

- id: network_chaos_ng
- module: krkn/scenario_plugins/network_chaos_ng/network_chaos_ng_scenario_plugin.py

### What

Create pods with `templates/network-chaos.j2` template and run `iptables` commands inside them to apply network chaos conditions like bandwidth limitations, latency, or packet loss to specific network interfaces. This is a more advanced and flexible version of the original network chaos scenario.


`krkn/scenario_plugins/network_chaos_ng/modules/templates/network-chaos.j2`  

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: {{pod_name}}
  namespace: {{namespace}}
spec:
  {% if host_network %}
  hostNetwork: true
  {%endif%}
  nodeSelector:
    kubernetes.io/hostname: {{target}}
  containers:
  - name: fedora
    imagePullPolicy: Always
    image: quay.io/krkn-chaos/krkn-network-chaos:latest
    securityContext:
      privileged: true
```

### Rollback

- need: yes
- resource: `Pod`

Set `delete_pod` callable to version file to clean up the chaos pods properly after the scenario duration.

## Node Actions Scenarios

- id: node_actions
- module: krkn/scenario_plugins/node_actions/node_actions_scenario_plugin.py

### What

Disrupts nodes as part of the cluster infrastructure by talking to the cloud API for AWS, Azure, GCP, OpenStack, Baremetal, VMware, Docker, Alibaba and IBMCloud. Various actions include:
- Start/stop/reboot/terminate nodes
- Crash or disrupt node services like kubelet
- Block network access
- Detach/attach storage
- Multiple implementations for different cloud providers

Note: the entrypoint class is `NodeActionsScenarioPlugin`

### Rollback

- need: partially
- resource: `Node` (restarting nodes, reattaching disks, etc.)

Some actions require explicit rollback (like reattaching disks or restarting stopped nodes), while others (like node_reboot) don't need explicit rollback as the node will recover automatically. The plugin tracks affected nodes and their status during scenarios to facilitate recovery.

## PVC Scenarios

- id: pvc
- module: krkn/scenario_plugins/pvc/pvc_scenario_plugin.py

### What

Use `fallocate` or `dd` to fill up the PVC with `target_fill_percentage` in `<mount_path>/kraken.tmp` temporary file.

### Rollback

- need: yes
- resource: `PersistentVolumeClaim` (deleting the temporary file)

We need to clean up the temporary file created in the PVC after the scenario duration to prevent filling up the PVC permanently. 

## Service Disruption Scenarios

- id: service_disruption
- module: krkn/scenario_plugins/service_disruption/service_disruption_scenario_plugin.py

### What

Will get namespaces with `namespace` or `label_selector` parameters, and then take randomly 1 namespace from them as the target namespace.

Delete all `service` and `pod` (including `DaemonSet`, `StatefulSet`, `ReplicaSet` and `Deployment` resources) in the cluster for target namespaces.

### Rollback

- need: yes
- resource: `Service`, `DaemonSet`, `StatefulSet`, `ReplicaSet`, `Deployment` (should restore the original resources)

We should record which target namespace we selected, and all the resources (`Service`, `DaemonSet`, `StatefulSet`, `ReplicaSet` and `Deployment` resources) before deleting them, so we can restore the resources from version file after the scenario duration.

## Service Hijacking Scenarios

- id: service_hijacking
- module: krkn/scenario_plugins/service_hijacking/service_hijacking_scenario_plugin.py

### What

Simulates fake HTTP responses from a workload targeted by a `Service` already deployed in the cluster. This scenario deploys a custom web service and modifies the target `Service` selector to direct traffic to this web service for a specified duration.

Will
- create the following resources:
    - namespaced `ConfigMap`
    - `Pod` (running Flask app)
- replace the `Service` selector with the hijacking service selector

### Rollback

- need: yes
- resource: `Service`, `Pod`, `ConfigMap` (should restore the original Service selector and delete the hijacking service resources)

We should set `replace_service_selector` and `undeploy_service_hijacking` callables to version file to restore the original `Service` selector and delete the hijacking service resources after the scenario duration.

## Shut Down Scenarios

- id: shut_down
- module: krkn/scenario_plugins/shut_down/shut_down_scenario_plugin.py

### What

Shuts down all nodes in a cluster (including master nodes) for a specified duration and then restarts them. This simulates a complete power outage scenario. Supports AWS, Azure, GCP, OpenStack, and IBMCloud providers.

### Rollback

- need: yes
- resource: `Node` (restarting nodes)

The plugin explicitly restarts all nodes after the specified outage duration and waits for them to return to running state. It tracks the affected nodes and their status during the scenario to ensure proper recovery.

## Syn Flood Scenarios

- id: syn_flood
- module: krkn/scenario_plugins/syn_flood/syn_flood_scenario_plugin.py

### What

Performs SYN flood attacks (a form of denial of service) with `pod` resource.

### Rollback

- need: yes
- resource: `Pod`

Set `delete_pod` callable to version file to clean up the SYN flood attack pod properly after the scenario duration.

## Time Actions Scenarios

- id: time_actions
- module: krkn/scenario_plugins/time_actions/time_actions_scenario_plugin.py 

### What

Manipulates the system time on `node` or `pod` resources.

### Rollback

- need: yes

The plugin must restore the correct system time after the scenario to prevent continued time-related issues on the affected nodes.

## Zone Outage Scenarios

- id: zone_outage
- module: krkn/scenario_plugins/zone_outage/zone_outage_scenario_plugin.py

### What

Simulates a failure in an entire availability zone/region by either:
1. Stopping all nodes in the zone (for GCP)
2. Implementing network ACL blocks (for AWS)
The scenario maintains the outage for a specified duration before recovery.

### Rollback

- need: yes
- resource: `Node` (for GCP), `Network ACL` (for AWS)

For node-based zone outages (GCP), the plugin explicitly starts all stopped nodes after the specified duration. For network-based outages (AWS), it restores the original network ACL rules to allow traffic again.


