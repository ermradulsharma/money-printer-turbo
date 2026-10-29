from fastapi import Depends, Request
from loguru import logger

from app.controllers import base
from app.controllers.v1.base import new_router
from app.models.exception import HttpException
from app.models.schema import (
    VideoScriptRequest,
    VideoScriptResponse,
    VideoSocialMetadataRequest,
    VideoSocialMetadataResponse,
    VideoTermsRequest,
    VideoTermsResponse,
)
from app.services import llm
from app.utils import utils

router = new_router(dependencies=[Depends(base.verify_token)])


@router.post(
    "/scripts",
    response_model=VideoScriptResponse,
    summary="Create a script for the video",
)
def generate_video_script(request: Request, body: VideoScriptRequest):
    request_id = (
        base.get_task_id(request)
        if request and hasattr(request, "headers")
        else "script-gen"
    )
    try:
        video_script = llm.generate_script(
            video_subject=body.video_subject,
            language=body.video_language,
            paragraph_number=body.paragraph_number,
            video_script_prompt=body.video_script_prompt,
            custom_system_prompt=body.custom_system_prompt,
        )
        if not video_script or str(video_script).startswith("Error:"):
            raise HttpException(
                task_id=request_id,
                status_code=500,
                message=f"{request_id}: failed to generate video script",
            )
        response = {"video_script": video_script}
        return utils.get_response(200, response)
    except HttpException:
        raise
    except Exception as exc:
        logger.error(
            f"failed to generate video script, request_id: {request_id}, error: {str(exc)}"
        )
        raise HttpException(
            task_id=request_id,
            status_code=500,
            message=f"{request_id}: failed to generate video script",
        )


@router.post(
    "/terms",
    response_model=VideoTermsResponse,
    summary="Generate video terms based on the video script",
)
def generate_video_terms(request: Request, body: VideoTermsRequest):
    request_id = (
        base.get_task_id(request)
        if request and hasattr(request, "headers")
        else "terms-gen"
    )
    try:
        video_terms = llm.generate_terms(
            video_subject=body.video_subject,
            video_script=body.video_script,
            amount=body.amount,
            match_script_order=body.match_materials_to_script,
        )
        if not isinstance(video_terms, list):
            raise HttpException(
                task_id=request_id,
                status_code=500,
                message=f"{request_id}: failed to generate video terms",
            )
        response = {"video_terms": video_terms}
        return utils.get_response(200, response)
    except HttpException:
        raise
    except Exception as exc:
        logger.error(
            f"failed to generate video terms, request_id: {request_id}, error: {str(exc)}"
        )
        raise HttpException(
            task_id=request_id,
            status_code=500,
            message=f"{request_id}: failed to generate video terms",
        )


@router.post(
    "/social-metadata",
    response_model=VideoSocialMetadataResponse,
    summary="Generate social publishing metadata",
)
def generate_video_social_metadata(
    request: Request, body: VideoSocialMetadataRequest
):
    request_id = (
        base.get_task_id(request)
        if request and hasattr(request, "headers")
        else "social-meta"
    )
    try:
        metadata = llm.generate_social_metadata(
            video_subject=body.video_subject,
            video_script=body.video_script,
            language=body.language,
            platform=body.platform,
        )
        if not isinstance(metadata, dict):
            raise HttpException(
                task_id=request_id,
                status_code=500,
                message=f"{request_id}: failed to generate social metadata",
            )
        return utils.get_response(200, metadata)
    except HttpException:
        raise
    except Exception as exc:
        logger.error(
            f"failed to generate social metadata, request_id: {request_id}, error: {str(exc)}"
        )
        raise HttpException(
            task_id=request_id,
            status_code=500,
            message=f"{request_id}: failed to generate social metadata",
        )
