# moetype

基于萌娘百科词条的输入法词库

词条来源于 [mw2fcitx](https://github.com/outloudvi/mw2fcitx) 以及手动添加，用于便利地输入动漫角色名和声优名等词汇。

<img width="424" height="212" alt="image" src="https://github.com/user-attachments/assets/84c59dd3-fe2f-41bb-81ac-57998a51da90" />

## 如何使用

在 Release 中按需下载适合的版本，将其挂载到一个 Rime 输入方案里（仓库现在只保留“带声调-无辅助码”版本，词库发布主要以 release 为主）

### 下载

- 在仓库的 Releases (发行版) 中下载 `*_moe.dict.yaml`

如果您熟悉命令行操作，推荐使用 [Scoop](https://scoop.sh/) 进行下载和更新，请确保您已安装小狼毫作为前端。

- 使用 Scoop (如果使用这一方法下载需使用方法 A 挂载)

  - 添加 bucket ([Github](https://github.com/abgox/abyss) 或 [Gitee](https://gitee.com/abgox/abyss))

    ```shell
    scoop bucket add abyss https://github.com/abgox/abyss
    ```

    ```shell
    scoop bucket add abyss https://gitee.com/abgox/abyss
    ```

  - 下载无声调版

    ```shell
    scoop install abyss/suiginko.moetype.toneless
    ```

  - 下载有声调版

    ```shell
    scoop install abyss/suiginko.moetype.tone
    ```

  - 下载自然码辅助码版

    ```shell
    scoop install abyss/suiginko.moetype.zrm
    ```

  - 下载墨奇辅助码版

    ```shell
    scoop install abyss/suiginko.moetype.moqi
    ```

  - 下载小鹤辅助码版

    ```shell
    scoop install abyss/suiginko.moetype.flypy
    ```

如果使用的辅助码不在发布列表中，也可以使用“一键生成辅助码版词库脚本.py”生成任意辅助码的自用版本

### 挂载 (仅以万象为例，其他方案请自行调整)

下载完成后，可以通过 `wanxiang.custom.yaml` 将自己的固定词库加入方案。

#### 方法 A：通过 Packs 扩展（推荐）

这种方式不需要修改主词库文件，自己的词库可以单独维护，后续更新也更加方便。

但有个前置约束一定要知道：

⚠️注意词库文件放在用户目录，不能折叠到 `dicts` 文件夹

因此如果有各种异读需求考虑方法B吧！

假设新词库文件命名为：`moqi_moetype.moqi`

其词库表头中的 `name` 需要保持一致：

词库表头示例

##### rime dictionary
---
name: moqi_moe
version: "LTS"
sort: by_weight
...

然后在 `wanxiang.custom.yaml` 中追加：

```
patch:
  translator/packs/+:
    - moqi_moe # 填写词库名称，不需要包含 .dict.yaml

```

重新部署后，该词库即可作为主词库的扩展参与输入。

#### 方法 B：自定义主词库

如果需要直接维护一套自己的完整主词库，可以复制根目录中的 `wanxiang.dict.yaml`，例如重命名为 `wanxianguser.dict.yaml`

同时将词库内部的 `name` 等信息修改为对应名称。

随后通过 Patch 将相关词库调用统一指向新的主词库：

```
wanxiang.custom.yaml
```

```
patch:
  translator/dictionary: wanxianguser
  user_dict_set/dictionary: wanxianguser
  add_user_dict/dictionary: wanxianguser
```

这种方式会直接替换方案原本调用的主词库，更适合已经了解万象词库结构和相关调用关系的用户。

## 协助修订

如果有修正和添加词条的建议，可以提出issues或discussions

或者填写 [在线表格](https://docs.qq.com/smartsheet/DQ29GemR6Z2JJeUd4?tab=t00i2h&viewId=v2JKhc)

qq 群 781639677
