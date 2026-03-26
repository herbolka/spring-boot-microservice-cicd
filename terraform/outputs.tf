output "cluster_endpoint" {
  value = aws_eks_cluster.my_cluster.endpoint
}

output "cluster_name" {
  value = aws_eks_cluster.my_cluster.name
}

output "cluster_version" {
  value = aws_eks_cluster.my_cluster.version
}

output "kubeconfig" {
  value = aws_eks_cluster.my_cluster.kubeconfig
}

output "node_group_role_arn" {
  value = aws_eks_node_group.my_node_group.iam_role_arn
}