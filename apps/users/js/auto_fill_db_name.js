(function($){
    $(document).ready(function() {
        function updateDbName() {
            var selectedOrg = $('#id_organization').val();
            if(selectedOrg) {
                $.ajax({
                    url: "/admin/get-org-db-name/",
                    data: { 'org_id': selectedOrg },
                    success: function(data) {
                        $('#id_organization_db_name').val(data.db_name);
                    }
                });
            } else {
                $('#id_organization_db_name').val('');
            }
        }

        $('#id_organization').change(updateDbName);
        updateDbName();  // for edit view
    });
})(django.jQuery);
