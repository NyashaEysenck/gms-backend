from ...schemas.application import ApplicationResponse

def build_application_response(application) -> ApplicationResponse:
    """Helper function to build consistent ApplicationResponse with all fields"""
    
    def get_field(app, camel_case_key: str, snake_case_key: str = None, default=None):
        """Unified field getter for both dict and object types"""
        if isinstance(app, dict):
            # Try camelCase first, then snake_case fallback
            snake_key = snake_case_key or camel_case_key.replace('_', '').lower()
            return app.get(camel_case_key, app.get(snake_key, default))
        else:
            # Object attribute access with snake_case preference
            snake_key = snake_case_key or camel_case_key
            return getattr(app, snake_key, default)
    
    def get_signoff_award_amount(app):
        """Get award amount from signoff_workflow consistently"""
        if isinstance(app, dict):
            return app.get("signoff_workflow", {}).get("award_amount")
        else:
            workflow = getattr(app, 'signoff_workflow', {})
            return workflow.get('award_amount') if workflow else None
    
    # Unified response building
    return ApplicationResponse(
        id=str(get_field(application, "_id", "id", "")),
        grant_id=get_field(application, "grantId", "grant_id", ""),
        applicant_name=get_field(application, "applicantName", "applicant_name", ""),
        email=get_field(application, "email", default=""),
        proposal_title=get_field(application, "proposalTitle", "proposal_title", ""),
        status=get_field(application, "status", default=""),
        submission_date=get_field(application, "submissionDate", "submission_date", ""),
        review_comments=get_field(application, "reviewComments", "review_comments", ""),
        biodata=get_field(application, "biodata"),
        deadline=get_field(application, "deadline"),
        proposal_file_name=get_field(application, "proposalFileName", "proposal_file_name"),
        proposal_file_size=get_field(application, "proposalFileSize", "proposal_file_size"),
        proposal_file_type=get_field(application, "proposalFileType", "proposal_file_type"),
        reviewHistory=get_field(application, "reviewHistory", default=[]),
        revision_count=get_field(application, "revisionCount", "revision_count"),
        original_submission_date=get_field(application, "originalSubmissionDate", "original_submission_date"),
        is_editable=get_field(application, "isEditable", "is_editable"),
        sign_off_approvals=get_field(application, "signOffApprovals", "sign_off_approvals"),
        award_amount=get_signoff_award_amount(application),
        contract_file_name=get_field(application, "contractFileName", "contract_file_name"),
        award_letter_generated=get_field(application, "awardLetterGenerated", "award_letter_generated"),
        signoff_workflow=get_field(application, "signoffWorkflow", "signoff_workflow")
    )
