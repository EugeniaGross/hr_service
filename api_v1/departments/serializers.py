from rest_framework import serializers

from departments.models import Department


class DepartmentTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = (
            "id",
            "name",
            "level",
            "children",
        )
        read_only_fields = ("level", )

    def get_children(self, obj):
        children = obj.children.all()
        if not children:
            return []
        return DepartmentTreeSerializer(children, many=True).data
    
    
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = (
            "id",
            "name",
            "parent",
        )
        
        read_only_fields = ("level", )
