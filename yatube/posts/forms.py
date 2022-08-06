from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка'
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относится пост'
        }
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Добавьте Ваш комментарий',
        }
        fields = ('text',)
