import os
import shutil
import io
import json
import asyncio
import tempfile
from pathlib import Path
from typing import List

import pytest

from .local_provider import LocalDocumentStorageProvider
from ...domain.entities.document import Document

REQUIRED_EXTS = ['.txt', '.text', '.md', '.markdown', '.pdf', '.docx']

def test_supported_formats():
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = LocalDocumentStorageProvider(data_path=tmpdir)
        formats = provider.get_supported_formats()
        for ext in REQUIRED_EXTS:
            assert ext in formats, f"missing supported format: {ext}"


async def setup_and_load(provider: LocalDocumentStorageProvider, base_src: Path):
    """创建 provider 并从 base_src 加载文档，断言与调试输出。"""
    docs = await provider.load_documents(source_path=str(base_src))
    assert isinstance(docs, list), 'load_documents 应返回列表'
    assert len(docs) == 6, '应有6个文件'
    print(f"[debug] loaded {len(docs)} docs from test1: {base_src}")
    for i, d in enumerate(docs):
        src = getattr(d, 'source_path', None) or getattr(d, 'source', None)
        print(f"[debug] doc[{i}] source={src}")
    return docs


async def save_documents(provider: LocalDocumentStorageProvider, docs, base_dst: Path) -> int:
    """保存文档到 base_dst，保留原文件名与后缀并断言存在。"""
    saved_count = 0
    for d in docs:
        valid = await provider.validate_document(d)
        assert valid is True, f"文档未通过验证: {getattr(d, 'source_path', None)}"
        ok, doc_id = await provider.save_document(d)
        assert ok is True, f"保存失败: {getattr(d, 'doc_id', None) or doc_id}"
        orig_src = getattr(d, 'source_path', None) or getattr(d, 'source', None) or ''
        orig_name = Path(orig_src).name
        saved_orig = base_dst / orig_name
        print(f"[debug] saved original copy path: {saved_orig}")
        assert saved_orig.exists(), f"原始文件副本不存在: {saved_orig}"
        saved_count += 1
    print(f"[debug] total saved docs to test2 ({base_dst}): {saved_count}")
    return saved_count


async def list_and_assert(provider: LocalDocumentStorageProvider, expected_count: int = 6) -> str:
    """列出文档并断言数量为 6，返回其中一个文档的 docid。"""
    infos = await provider.list_documents()
    assert isinstance(infos, list), "list_documents 应返回列表"
    print(f"[debug] list_documents count={len(infos)}")
    assert len(infos) == expected_count, f"list_documents 应返回 {expected_count} 个条目"
    for j, info in enumerate(infos):
        print(f"[debug] info[{j}] id={info.get('id')} source={info.get('source')} meta={info.get('metadata')}")
    # 选择第一个包含 id 的条目返回
    chosen_id = None
    for info in infos:
        if isinstance(info, dict) and info.get('id'):
            chosen_id = info['id']
            break
    assert chosen_id, "未找到有效的文档ID"
    return chosen_id

async def get_and_assert(provider: LocalDocumentStorageProvider, document_id: str):
    """根据 document_id 调用 get_document 并断言基本属性。"""
    fetched = await provider.get_document(document_id)
    assert fetched is not None, '未能读取到文档'
    assert fetched.doc_id == document_id
    print(f"[debug] fetched doc_id={fetched.doc_id} content={fetched.content[:20]}...")


async def delete_and_assert(provider: LocalDocumentStorageProvider, document_id: str):
    """删除指定文档并断言文件与映射均被清理，且无法再读取。"""
    ok = await provider.delete_document(document_id)
    assert ok is True, f"删除失败: {document_id}"

    # 读取应返回 None
    fetched = await provider.get_document(document_id)
    assert fetched is None, "删除后仍能读取到文档"


@pytest.mark.asyncio
async def test_load_and_crud_interfaces_for_all_formats():
        
        # 使用相对路径：以当前测试文件所在目录为基准
        base_dir = Path(__file__).parent
        print(f"[debug] current test dir: {base_dir}")
        base_src = base_dir / 'test1'
        base_dst = base_dir / 'test2'
        base_dst.mkdir(parents=True, exist_ok=True)

        # 清空目标目录下的所有文件/子目录，确保干净环境
        print(f"[debug] clearing base_dst directory: {base_dst}")
        for item in base_dst.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(f"[warn] failed to remove {item}: {e}")

        # 重置 provider 并加载、保存、列出
        provider = LocalDocumentStorageProvider(data_path=str(base_dst))
        docs = await setup_and_load(provider, base_src)
        await save_documents(provider, docs, base_dst)
        doc_id = await list_and_assert(provider, expected_count=6)
        await get_and_assert(provider, document_id=doc_id)
        await delete_and_assert(provider, document_id=doc_id)
        


